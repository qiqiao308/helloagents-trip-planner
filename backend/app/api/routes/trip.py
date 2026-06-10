"""旅行规划 API 路由"""

import logging
from fastapi import APIRouter, HTTPException

from app.models import TripPlan, TripPlanRequest
from app.agents import TripPlannerAgent
from app.services.unsplash_service import UnsplashService
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trip", tags=["trip"])

# 全局单例
_planner: TripPlannerAgent | None = None
_unsplash: UnsplashService | None = None


def _get_planner() -> TripPlannerAgent:
    global _planner
    if _planner is None:
        _planner = TripPlannerAgent()
    return _planner


def _get_unsplash() -> UnsplashService:
    global _unsplash
    if _unsplash is None:
        _unsplash = UnsplashService(get_settings().unsplash_access_key)
    return _unsplash


@router.post("/plan", response_model=TripPlan)
async def create_trip_plan(request: TripPlanRequest) -> TripPlan:
    """
    生成旅行计划

    - 调用多智能体系统搜索景点、天气、酒店
    - 整合信息生成完整行程
    - 为景点补充图片（来自 Unsplash）
    """
    logger.info(f"收到旅行规划请求: {request.city} {request.days}天")

    try:
        planner = _get_planner()
        trip_plan = await planner.plan_trip(request)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"规划失败: {e}")
        raise HTTPException(status_code=500, detail=f"旅行规划生成失败: {str(e)}")

    # 为景点获取 Unsplash 图片
    try:
        unsplash = _get_unsplash()
        for day in trip_plan.days:
            for attraction in day.attractions:
                if not attraction.image_url:
                    logger.info(f"正在为景点 '{attraction.name}' 获取图片...")
                    image_url = await unsplash.get_photo_url(
                        f"{attraction.name} {trip_plan.city}"
                    )
                    attraction.image_url = image_url
                    if image_url:
                        logger.info(f"成功获取图片: {attraction.name}")
                    else:
                        logger.warning(f"未能获取图片: {attraction.name}")
    except Exception as e:
        logger.warning(f"获取图片失败（非致命）: {e}")

    return trip_plan
