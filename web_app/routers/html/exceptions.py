from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from shared.utils.exceptions import UserNotFoundError


async def user_not_found_handler(request: Request, exc: Exception)-> JSONResponse | RedirectResponse:
    status_code = getattr(exc, "status_code", 401)

    # Для API-запросов возвращаем JSON
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status_code,
            content={"detail": str(exc)},
        )
    # HTML-страницы: редиректим на главную
    print("user_not_found_handler: отправил на главную, нет пользователя")
    return RedirectResponse(url="/", status_code=303)