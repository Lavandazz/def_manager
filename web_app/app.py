"""
Запуск сервера: 
fastapi dev
uvicorn app.app:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin

from shared.config.db.database import UnitOfWork
from shared.config.settings_folders import WEB_APP
from shared.config.settings_env import settings
from shared.utils.exceptions import UserNotFoundError
from shared.config.db.db_config import async_sessionmaker

from web_app.admin.auth import AdminAuth
from web_app.admin.dependensy import get_user_service
from web_app.admin.views import VIEWS
from web_app.routers.api.api import router as api_router
from web_app.routers.api.user.api_user import router as api_user_router
from web_app.routers.api.user.api_cases import router as api_cases_router

from web_app.routers.html.exceptions import user_not_found_handler
from web_app.routers.html.user import router as user_router
from web_app.routers.html.case import router as case_router
from web_app.routers.html.index import router as main_router
from web_app.routers.html.courts import router as court_router
from web_app.routers.html.debtor import router as debtor_router
from web_app.routers.html.help import router as help_router
from web_app.routers.html.parser_rout import router as parser_router


async def init_db():
    """Создаёт роли и администратора, если их нет."""
    uow = UnitOfWork(async_sessionmaker)
    async with uow:
        service = get_user_service(uow.session)
        await service.init_defaults()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()      # инициализация ролей
    yield

app = FastAPI(debug=True, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=f"{WEB_APP}/static"), name="static")

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

app.add_exception_handler(UserNotFoundError, user_not_found_handler)

admin = Admin(app, session_maker=async_sessionmaker, authentication_backend=AdminAuth(secret_key=settings.SECRET_KEY, session_maker=async_sessionmaker))
for view in VIEWS:
    admin.add_view(view)

app.include_router(api_router, prefix="/api")
app.include_router(api_user_router, prefix="/api/user")
app.include_router(api_cases_router, prefix="/api/cases")
app.include_router(main_router)
app.include_router(help_router, prefix="/help")
app.include_router(user_router, prefix="/user")
app.include_router(case_router, prefix="/user/cases")
app.include_router(court_router, prefix="/user/courts")
app.include_router(debtor_router, prefix="/user/debtor")

app.include_router(parser_router, prefix="/parsing")
