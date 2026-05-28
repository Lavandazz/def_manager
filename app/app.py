"""
Запуск сервера: 
fastapi dev
"""
from fastapi import FastAPI
from app.routers.api.api import router as api_router
from app.routers.api.user.api import router as user_router


app = FastAPI(debug=True)

app.include_router(api_router, prefix="/api")
app.include_router(user_router, prefix="/api/user")
