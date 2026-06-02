"""
Запуск сервера: 
fastapi dev
"""

from fastapi import FastAPI
from app.routers.api.api import router as api_router
from app.routers.api.user.api_user import router as api_user_router
from app.routers.api.user.api_cases import router as api_cases_router
from app.routers.html.user import router as user_router
from app.routers.html.case import router as case_router
from app.routers.html.index import router as main_router

app = FastAPI(debug=True)

app.include_router(api_router, prefix="/api")
app.include_router(api_user_router, prefix="/api/user")
app.include_router(api_cases_router, prefix="/api/user/case")
app.include_router(main_router)
app.include_router(user_router, prefix="/user")
app.include_router(case_router, prefix="/user/case")


