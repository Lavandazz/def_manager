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


st = [
    57237.30,
    54366.30,
    17943.05,
    5570.53,
    34633.33,
    5475.91,
    8624.56,
    27263.00,
    27554,
    2121.92,
    10609.58,
    2053.47,
    38730.75,
    42573.55

]
print(sum(st))
print(len(st))