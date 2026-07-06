from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from coop_shared.config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
replica_engine = create_async_engine(settings.replica_database_url, echo=False, pool_pre_ping=True)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
ReplicaSessionLocal = async_sessionmaker(replica_engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def get_replica_db() -> AsyncGenerator[AsyncSession, None]:
    async with ReplicaSessionLocal() as session:
        yield session
