from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.api.api import router as api_router
from app.routers.api.user.api_cases import router as api_cases_router
from app.routers.api.user.api_user import router as api_user_router
from app.utils.dependensy import get_case_service, get_token_service, get_user_service, get_verify_user
from config.db.models import Case, User


def create_test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(api_router, prefix="/api")
    test_app.include_router(api_user_router, prefix="/api/user")
    test_app.include_router(api_cases_router, prefix="/api/cases")
    return test_app


@pytest.fixture
def test_app():
    return create_test_app()


@pytest.fixture
def mock_user() -> User:
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
        telegram_id=12345,
    )


@pytest.fixture
def mock_case() -> Case:
    return Case(
        id=1,
        number_case="A40-12345/2024",
        debtor="ООО Тест",
        id_user=1,
        status=0,
    )


@pytest.fixture
def mock_case_service():
    return AsyncMock()


@pytest.fixture
def mock_user_service():
    return AsyncMock()


@pytest.fixture
def mock_token_service():
    return AsyncMock()


@pytest.fixture
def client(test_app, mock_user):
    test_app.dependency_overrides[get_verify_user] = lambda: mock_user
    with TestClient(test_app) as test_client:
        yield test_client
    test_app.dependency_overrides.clear()


@pytest.fixture
def client_without_user(test_app):
    test_app.dependency_overrides[get_verify_user] = lambda: None
    with TestClient(test_app) as test_client:
        yield test_client
    test_app.dependency_overrides.clear()


@pytest.fixture
def client_with_case_service(test_app, mock_user, mock_case_service):
    test_app.dependency_overrides[get_verify_user] = lambda: mock_user
    test_app.dependency_overrides[get_case_service] = lambda: mock_case_service
    with TestClient(test_app) as test_client:
        yield test_client
    test_app.dependency_overrides.clear()


@pytest.fixture
def client_with_user_service(test_app, mock_user_service):
    test_app.dependency_overrides[get_user_service] = lambda: mock_user_service
    with TestClient(test_app) as test_client:
        yield test_client
    test_app.dependency_overrides.clear()


@pytest.fixture
def client_with_token_service(test_app, mock_token_service):
    test_app.dependency_overrides[get_token_service] = lambda: mock_token_service
    with TestClient(test_app) as test_client:
        yield test_client
    test_app.dependency_overrides.clear()
