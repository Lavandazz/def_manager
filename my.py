# from sqlalchemy import select
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker

# from config.db.models import User
# from config.settings_env import settings

# engine = create_engine(settings.get_sync_db_url())
# session = sessionmaker(bind=engine)

# with session() as s:
#     stmt = select(User).where(User.username == "Марина")
#     result = s.execute(stmt)
#     user = result.scalars().first()
#     print("User", user.username)

from datetime import date, datetime, timedelta


def check_date_earlier(check_date: date) -> bool:
    """Проверка даты - 1 месяц"""
    current_month = datetime.now().date()
    date_earlier = current_month - timedelta(days=30)
    if check_date.month in (
        date_earlier.month, current_month.month) and check_date.year == current_month.year:
        return True
    return False


