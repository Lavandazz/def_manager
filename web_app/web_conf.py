from fastapi.templating import Jinja2Templates
from shared.config.settings_folders import WEB_APP

templates = Jinja2Templates(directory=f"{WEB_APP}/templates")