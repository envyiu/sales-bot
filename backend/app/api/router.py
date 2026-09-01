from fastapi import APIRouter

from app.api.routes.chat import router as chat_router
from app.api.routes.products import router as products_router


api_router = APIRouter(prefix="/api")
api_router.include_router(products_router, prefix="/products", tags=["products"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
