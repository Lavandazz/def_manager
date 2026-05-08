"""
Запуск сервера: fastapi dev
"""
from fastapi import FastAPI
from routers.api.api import router as api_router


app = FastAPI(debug=True)

app.include_router(api_router, prefix="/api")
