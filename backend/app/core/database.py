from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# connect_args differs by driver: asyncpg accepts ssl=False, aiosqlite does not.
_db_url = settings.DATABASE_URL
if _db_url.startswith("sqlite"):
    _connect_args: dict = {"check_same_thread": False}
else:
    _connect_args = {"ssl": False}

engine = create_async_engine(
    _db_url,
    echo=False,
    connect_args=_connect_args,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
