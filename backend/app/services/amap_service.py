"""高德地图 API 服务 —— 封装 POI 搜索和天气查询"""

import logging
import httpx

logger = logging.getLogger(__name__)


class AMapService:
    """高德地图 Web 服务"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3"

    async def _get(self, path: str, params: dict) -> dict:
        """通用 GET 请求"""
        params["key"] = self.api_key
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{self.base_url}{path}", params=params)
            resp.raise_for_status()
            return resp.json()

    async def text_search(self, keywords: str, city: str, page: int = 1) -> dict:
        """POI 关键词搜索"""
        params = {
            "keywords": keywords,
            "city": city,
            "offset": 10,
            "page": page,
            "extensions": "all",
        }
        return await self._get("/place/text", params)

    async def weather_info(self, city: str) -> dict:
        """天气查询"""
        # 先获取城市 adcode
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://restapi.amap.com/v3/config/district",
                params={"key": self.api_key, "keywords": city, "subdistrict": 0},
            )
            resp.raise_for_status()
            district = resp.json()

        adcode = city
        if district.get("districts") and len(district["districts"]) > 0:
            adcode = district["districts"][0].get("adcode", city)

        return await self._get("/weather/weatherInfo", {"city": adcode, "extensions": "all"})
