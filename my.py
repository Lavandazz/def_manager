from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.db.models import User
from config.settings_env import settings

engine = create_engine(settings.get_sync_db_url())
session = sessionmaker(bind=engine)

with session() as s:
    stmt = select(User).where(User.username == "Марина")
    result = s.execute(stmt)
    user = result.scalars().first()
    print("User", user.username)
