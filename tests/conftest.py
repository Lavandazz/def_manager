from datetime import date
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from web_app.routers.api.api import router as api_router
from web_app.routers.api.user.api_cases import router as api_cases_router
from web_app.routers.api.user.api_user import router as api_user_router
from web_app.routers.html.case import router as case_router
from web_app.routers.html.courts import router as court_router
from web_app.routers.html.debtor import router as debtor_router
from web_app.routers.html.help import router as help_router
from web_app.routers.html.index import router as main_router
from web_app.routers.html.user import router as user_router
from web_app.utils.dependensy import (
    get_bank_service,
    get_case_service,
    get_court_service,
    get_debtor_service,
    get_document_service,
    get_mail_service,
    get_optional_user,
    get_redis_service,
    get_region_service,
    get_residential_address_service,
    get_token_service,
    get_user_service,
    get_verify_user,
)
from shared.config.db.models import Case, Debtor, DebtorType, User
from shared.core.services.debtor_service import DebtorDetail


def create_test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(api_router, prefix="/api")
    test_app.include_router(api_user_router, prefix="/api/user")
    test_app.include_router(api_cases_router, prefix="/api/cases")
    return test_app


def create_html_test_app() -> FastAPI:
    """Тестовое приложение с HTML-роутами (как в web_app/app.py)."""
    test_app = FastAPI()
    test_app.include_router(main_router)
    test_app.include_router(help_router, prefix="/help")
    test_app.include_router(user_router, prefix="/user")
    test_app.include_router(case_router, prefix="/user/cases")
    test_app.include_router(court_router, prefix="/user/courts")
    test_app.include_router(debtor_router, prefix="/user/debtor")
    return test_app


@pytest.fixture
def test_app():
    return create_test_app()


@pytest.fixture
def html_app():
    return create_html_test_app()


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
def mock_debtor() -> Debtor:
    return Debtor(
        id=10,
        name="Иванов Иван Иванович",
        debtor_type=DebtorType.PHYSICAL,
        inn=123456789012,
        snils=12345678901,
        birthday=date(1990, 1, 15),
    )


@pytest.fixture
def mock_case() -> Case:
    """Простой Case для API-тестов (без relationship, чтобы JSON не зацикливался)."""
    return Case(
        id=1,
        number_case="A40-12345/2024",
        debtor_name="ООО Тест",
        id_user=1,
        status=0,
    )


@pytest.fixture
def html_case(mock_debtor) -> Case:
    """Case с должником для HTML-шаблонов."""
    case = Case(
        id=1,
        number_case="A40-12345/2024",
        debtor_name=mock_debtor.name,
        id_user=1,
        status=0,
        debtor_id=mock_debtor.id,
        date_case=date(2024, 3, 1),
    )
    case.debtor = mock_debtor
    return case


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
def mock_debtor_service():
    return AsyncMock()


@pytest.fixture
def mock_court_service():
    return AsyncMock()


@pytest.fixture
def mock_bank_service():
    service = AsyncMock()
    service.list_banks.return_value = []
    return service


@pytest.fixture
def mock_region_service():
    service = AsyncMock()
    service.list_regions.return_value = []
    return service


@pytest.fixture
def mock_residential_service():
    service = AsyncMock()
    service.list_addresses.return_value = []
    return service


@pytest.fixture
def mock_mail_service():
    service = AsyncMock()
    service.create_mail_address.return_value = AsyncMock(id=1)
    return service


@pytest.fixture
def mock_document_service():
    return AsyncMock()


@pytest.fixture
def mock_redis_service():
    service = AsyncMock()
    service.redis_client = AsyncMock()
    return service


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


@pytest.fixture
def cached_cases(html_case, mock_debtor):
    """Кэш дел в формате dict (как после CaseSchema.model_dump())."""
    return [
        {
            "id": html_case.id,
            "number_case": html_case.number_case,
            "debtor_id": mock_debtor.id,
            "debtor": {"id": mock_debtor.id, "name": mock_debtor.name},
        }
    ]


@pytest.fixture
def patch_cases_cache(monkeypatch, cached_cases):
    """Мокает кэш дел во всех HTML-модулях, где он импортирован."""
    async def _get(user_id):
        return cached_cases

    async def _save(user_id, cases):
        return None

    modules = (
        "web_app.routers.html.index",
        "web_app.routers.html.user",
        "web_app.routers.html.case",
        "web_app.routers.html.debtor",
        "web_app.routers.html.courts",
    )
    for mod in modules:
        monkeypatch.setattr(f"{mod}.get_cases_from_cache", _get)
        if mod == "web_app.routers.html.index":
            monkeypatch.setattr(f"{mod}.save_cases_to_cache", _save)


@pytest.fixture
def patch_empty_cases_cache(monkeypatch):
    async def _get(user_id):
        return None

    async def _save(user_id, cases):
        return None

    modules = (
        "web_app.routers.html.index",
        "web_app.routers.html.user",
        "web_app.routers.html.case",
        "web_app.routers.html.debtor",
        "web_app.routers.html.courts",
    )
    for mod in modules:
        monkeypatch.setattr(f"{mod}.get_cases_from_cache", _get)
        if mod == "web_app.routers.html.index":
            monkeypatch.setattr(f"{mod}.save_cases_to_cache", _save)


@pytest.fixture
def html_client(html_app, mock_user, patch_cases_cache):
    html_app.dependency_overrides[get_optional_user] = lambda: mock_user
    with TestClient(html_app) as test_client:
        yield test_client
    html_app.dependency_overrides.clear()


@pytest.fixture
def html_client_anon(html_app, patch_empty_cases_cache):
    html_app.dependency_overrides[get_optional_user] = lambda: None
    with TestClient(html_app) as test_client:
        yield test_client
    html_app.dependency_overrides.clear()


@pytest.fixture
def html_client_full(
    html_app,
    mock_user,
    mock_user_service,
    mock_case_service,
    mock_debtor_service,
    mock_court_service,
    mock_bank_service,
    mock_region_service,
    mock_residential_service,
    mock_mail_service,
    mock_document_service,
    mock_redis_service,
    patch_cases_cache,
):
    """Авторизованный клиент со всеми сервисами для HTML-роутов."""
    html_app.dependency_overrides[get_optional_user] = lambda: mock_user
    html_app.dependency_overrides[get_user_service] = lambda: mock_user_service
    html_app.dependency_overrides[get_case_service] = lambda: mock_case_service
    html_app.dependency_overrides[get_debtor_service] = lambda: mock_debtor_service
    html_app.dependency_overrides[get_court_service] = lambda: mock_court_service
    html_app.dependency_overrides[get_bank_service] = lambda: mock_bank_service
    html_app.dependency_overrides[get_region_service] = lambda: mock_region_service
    html_app.dependency_overrides[get_residential_address_service] = lambda: mock_residential_service
    html_app.dependency_overrides[get_mail_service] = lambda: mock_mail_service
    html_app.dependency_overrides[get_document_service] = lambda: mock_document_service
    html_app.dependency_overrides[get_redis_service] = lambda: mock_redis_service
    with TestClient(html_app) as test_client:
        yield test_client
    html_app.dependency_overrides.clear()


@pytest.fixture
def html_client_anon_services(
    html_app,
    mock_user_service,
    mock_case_service,
    mock_debtor_service,
    mock_court_service,
    mock_redis_service,
    patch_empty_cases_cache,
):
    """Неавторизованный клиент с моками сервисов."""
    html_app.dependency_overrides[get_optional_user] = lambda: None
    html_app.dependency_overrides[get_user_service] = lambda: mock_user_service
    html_app.dependency_overrides[get_case_service] = lambda: mock_case_service
    html_app.dependency_overrides[get_debtor_service] = lambda: mock_debtor_service
    html_app.dependency_overrides[get_court_service] = lambda: mock_court_service
    html_app.dependency_overrides[get_redis_service] = lambda: mock_redis_service
    with TestClient(html_app) as test_client:
        yield test_client
    html_app.dependency_overrides.clear()


@pytest.fixture
def mock_debtor_detail(mock_debtor) -> DebtorDetail:
    return DebtorDetail(debtor=mock_debtor, accounts=[])
