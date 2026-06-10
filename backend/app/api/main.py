"""FastAPI 应用入口"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.trip import router as trip_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="智能旅行助手 API",
    description="基于 LangChain 多智能体的旅行规划服务",
    version="1.0.0",
)

# CORS 配置 —— 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "智能旅行助手 API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
