"""
Запуск сервера: 
fastapi dev
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.api.api import router as api_router
from app.routers.api.user.api_user import router as api_user_router
from app.routers.api.user.api_cases import router as api_cases_router
from app.routers.html.user import router as user_router
from app.routers.html.case import router as case_router
from app.routers.html.index import router as main_router
from app.routers.html.courts import router as court_router

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=(),
    allow_methods=("GET",),
    allow_headers=(),
    allow_credentials=False,
    allow_origin_regex=None,
    allow_private_network=False,
    expose_headers=(),
    max_age=600,
)


app.include_router(api_router, prefix="/api")
app.include_router(api_user_router, prefix="/api/user")
app.include_router(api_cases_router, prefix="/api/cases")
app.include_router(main_router)
app.include_router(user_router, prefix="/user")
app.include_router(case_router, prefix="/user/cases")
app.include_router(court_router, prefix="/user/courts")

