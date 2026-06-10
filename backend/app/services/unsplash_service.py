"""Unsplash 图片服务 —— 为景点搜索配图"""

import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


class UnsplashService:
    """Unsplash 图片服务"""

    def __init__(self, access_key: str):
        self.access_key = access_key
        self.base_url = "https://api.unsplash.com"

    async def search_photos(self, query: str, per_page: int = 5) -> list[dict]:
        """搜索图片"""
        if not self.access_key:
            return []
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/search/photos",
                    params={
                        "query": query,
                        "per_page": per_page,
                        "client_id": self.access_key,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                return [
                    {
                        "url": r["urls"]["regular"],
                        "description": r.get("description", ""),
                        "photographer": r["user"]["name"],
                    }
                    for r in results
                ]
        except Exception as e:
            logger.warning(f"Unsplash 搜索失败: {e}")
            return []

    async def get_photo_url(self, query: str) -> Optional[str]:
        """获取单张图片 URL"""
        # 先用原始query搜索
        photos = await self.search_photos(query, per_page=1)
        if photos:
            return photos[0]["url"]
        
        # 如果失败，尝试用英文关键词搜索（去掉中文，保留英文部分）
        import re
        # 提取英文部分或使用通用关键词
        english_query = re.sub(r'[^\x00-\x7F]', '', query).strip()
        if english_query:
            photos = await self.search_photos(english_query, per_page=1)
            if photos:
                return photos[0]["url"]
        
        # 最后尝试通用旅游关键词
        generic_queries = ["travel", "tourism", "landmark", "architecture", "scenic"]
        for generic in generic_queries:
            photos = await self.search_photos(generic, per_page=1)
            if photos:
                return photos[0]["url"]
        
        return None
