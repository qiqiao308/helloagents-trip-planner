"""多智能体旅行规划器 —— 基于 LangChain 实现

四个专门的 Agent：
1. AttractionSearchAgent - 景点搜索
2. WeatherQueryAgent   - 天气查询
3. HotelAgent          - 酒店推荐
4. PlannerAgent        - 行程整合规划
"""

import json
import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from app.config import get_settings
from app.models import TripPlan, TripPlanRequest
from app.services.amap_service import AMapService
from app.agents.prompts import (
    ATTRACTION_AGENT_SYSTEM,
    WEATHER_AGENT_SYSTEM,
    HOTEL_AGENT_SYSTEM,
    PLANNER_AGENT_SYSTEM,
)

logger = logging.getLogger(__name__)


# ── 工具工厂（绑定 AMap 服务实例）─────────────────────

def _make_amap_tools(amap: AMapService):
    """创建 LangChain 工具 —— 封装高德地图 API 调用"""

    @tool
    async def search_attractions(keywords: str, city: str) -> str:
        """搜索景点。keywords: 搜索关键词（如"景点"、"博物馆"、"公园"），city: 城市名称"""
        result = await amap.text_search(keywords, city)
        pois = result.get("pois", [])
        if not pois:
            return json.dumps({"pois": [], "message": f"未找到与'{keywords}'相关的景点"}, ensure_ascii=False)
        simplified = []
        for p in pois:
            loc = p.get("location", "0,0").split(",")
            simplified.append({
                "name": p.get("name", ""),
                "address": p.get("address", ""),
                "location": {"longitude": float(loc[0]) if len(loc) == 2 else 0,
                            "latitude": float(loc[1]) if len(loc) == 2 else 0},
                "rating": float(p.get("biz_ext", {}).get("rating", 4.0) or 4.0),
                "category": p.get("type", "景点"),
            })
        return json.dumps({"pois": simplified, "count": len(simplified)}, ensure_ascii=False)

    @tool
    async def search_hotels(keywords: str, city: str) -> str:
        """搜索酒店。keywords: 搜索关键词（如"经济型酒店"、"豪华酒店"），city: 城市名称"""
        result = await amap.text_search(keywords, city)
        pois = result.get("pois", [])
        if not pois:
            return json.dumps({"pois": [], "message": f"未找到与'{keywords}'相关的酒店"}, ensure_ascii=False)
        simplified = []
        for p in pois:
            loc = p.get("location", "0,0").split(",")
            simplified.append({
                "name": p.get("name", ""),
                "address": p.get("address", ""),
                "location": {"longitude": float(loc[0]) if len(loc) == 2 else 0,
                            "latitude": float(loc[1]) if len(loc) == 2 else 0},
                "rating": float(p.get("biz_ext", {}).get("rating", 4.0) or 4.0),
                "type": p.get("type", "酒店"),
            })
        return json.dumps({"pois": simplified, "count": len(simplified)}, ensure_ascii=False)

    @tool
    async def query_weather(city: str) -> str:
        """查询城市天气。city: 城市名称（如"北京"）"""
        result = await amap.weather_info(city)
        forecasts = result.get("forecasts", [])
        if not forecasts:
            return json.dumps({"forecasts": [], "message": "未获取到天气信息"}, ensure_ascii=False)
        simplified = []
        for f in forecasts:
            for cast in f.get("casts", []):
                simplified.append({
                    "date": cast.get("date", ""),
                    "day_weather": cast.get("dayweather", ""),
                    "night_weather": cast.get("nightweather", ""),
                    "day_temp": cast.get("daytemp", "0"),
                    "night_temp": cast.get("nighttemp", "0"),
                    "wind_direction": cast.get("daywind", ""),
                    "wind_power": cast.get("daypower", ""),
                })
        return json.dumps({"forecasts": simplified, "count": len(simplified)}, ensure_ascii=False)

    return [search_attractions, search_hotels, query_weather]


# ── Agent 运行器 ────────────────────────────────────────

class TripPlannerAgent:
    """多智能体旅行规划器 —— 协调 4 个专门 Agent 完成旅行规划"""

    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            temperature=0.2,
            max_tokens=4000,
        )
        # 用于生成最终计划的高温模型（更有创意）
        self.planner_llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            temperature=0.7,
            max_tokens=8000,
        )
        self.amap = AMapService(settings.amap_api_key)
        self._tools = _make_amap_tools(self.amap)
        self._tool_map = {t.name: t for t in self._tools}

    async def _run_agent(self, system_prompt: str, user_query: str, tools: list) -> str:
        """通用 Agent 运行器 —— LLM + 工具调用循环"""
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_query)]

        # 绑定工具
        llm_with_tools = self.llm.bind_tools(tools)
        response = await llm_with_tools.ainvoke(messages)

        # 处理工具调用
        max_rounds = 3
        for _ in range(max_rounds):
            tool_calls = getattr(response, "tool_calls", None) or []
            if not tool_calls:
                break

            messages.append(response)
            for tc in tool_calls:
                tool_name = tc.get("name", "")
                tool_args = tc.get("args", {})
                logger.info(f"Agent 调用工具: {tool_name}({tool_args})")

                if tool_name in self._tool_map:
                    result = await self._tool_map[tool_name].ainvoke(tool_args)
                    messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
                else:
                    messages.append(ToolMessage(
                        content=f"未知工具: {tool_name}", tool_call_id=tc["id"]
                    ))

            response = await llm_with_tools.ainvoke(messages)

        return response.content

    def _extract_json(self, text: str) -> str:
        """从 LLM 输出中提取 JSON 内容"""
        # 处理 ```json ... ``` 包裹的情况
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1].strip()
        return text

    async def plan_trip(self, request: TripPlanRequest) -> TripPlan:
        """
        执行完整的旅行规划流程：
        1. 景点搜索  → AttractionSearchAgent
        2. 天气查询  → WeatherQueryAgent
        3. 酒店搜索  → HotelAgent
        4. 整合规划  → PlannerAgent
        """
        # ── 步骤 1：景点搜索 ──
        logger.info(f"[1/4] 搜索 {request.city} 的 {request.preferences} 景点...")
        attraction_query = f"请搜索{request.city}的{request.preferences}相关景点，至少搜索3个不同关键词。"
        attraction_raw = await self._run_agent(
            ATTRACTION_AGENT_SYSTEM, attraction_query, self._tools
        )
        attraction_text = self._extract_json(attraction_raw)
        logger.info(f"景点搜索结果: {attraction_text[:200]}...")

        # ── 步骤 2：天气查询 ──
        logger.info(f"[2/4] 查询 {request.city} 天气...")
        weather_raw = await self._run_agent(
            WEATHER_AGENT_SYSTEM,
            f"请查询{request.city}的天气信息",
            self._tools,
        )

        # ── 步骤 3：酒店搜索 ──
        logger.info(f"[3/4] 搜索 {request.city} 的 {request.accommodation}...")
        hotel_raw = await self._run_agent(
            HOTEL_AGENT_SYSTEM,
            f"请搜索{request.city}的{request.accommodation}",
            self._tools,
        )

        # ── 步骤 4：整合规划 ──
        logger.info("[4/4] 整合生成旅行计划...")
        planner_query = f"""
请根据以下信息生成{request.city}的{request.days}日旅行计划：

**用户需求：**
- 目的地: {request.city}
- 日期: {request.start_date} 至 {request.end_date}
- 天数: {request.days}天
- 偏好: {request.preferences}
- 预算: {request.budget}
- 交通方式: {request.transportation}
- 住宿类型: {request.accommodation}

**景点信息：**
{attraction_text}

**天气信息：**
{self._extract_json(weather_raw)}

**酒店信息：**
{self._extract_json(hotel_raw)}

请根据以上数据生成详细的旅行计划（严格按照 JSON 格式返回）。
"""
        planner_response = await self.planner_llm.ainvoke([
            SystemMessage(content=PLANNER_AGENT_SYSTEM),
            HumanMessage(content=planner_query),
        ])
        plan_json = self._extract_json(planner_response.content)
        logger.info(f"规划结果: {plan_json[:500]}...")

        # ── 解析为 Pydantic 模型 ──
        try:
            trip_plan = TripPlan.model_validate_json(plan_json)
        except Exception as e:
            logger.error(f"JSON 解析失败: {e}\n原始输出: {plan_json[:1000]}")
            raise ValueError(f"行程规划解析失败: {e}")

        return trip_plan
