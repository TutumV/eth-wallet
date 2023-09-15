import asyncio

import asyncpg
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.main import app
from app.model import Base, Wallet


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def engine():
    return create_async_engine(settings.database_uri)


@pytest.fixture
def session(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(autouse=True, scope="session")
async def setup_database():
    conn = await asyncpg.connect(
        database="postgres",
        user=settings.database_user,
        password=settings.database_password,
        host=settings.database_host,
        port=settings.database_port,
    )
    await conn.execute(f'DROP DATABASE IF EXISTS "{settings.database_name}"')
    await conn.execute(f'CREATE DATABASE "{settings.database_name}" OWNER "{settings.database_user}"')


@pytest_asyncio.fixture(scope="function")
async def prepare_database(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(prepare_database):
    async with AsyncClient(app=app, base_url='http://127.0.0.1') as c:
        yield c


@pytest.fixture
def wallet_data():
    return dict(
        address='0x7e13F900472204F062c270B5E9Cb3CF127B08F18',
        private_key='42ba349b3c2120f30e4210c9086515b8e231a2047af84767b584ec35f7e25494',
        mnemonic='alter phrase erupt aun glory media want aun noble tooth fine aun',
        leaf=0,
    )


@pytest_asyncio.fixture(scope="function")
async def wallets(session):
    data = [
        Wallet(
            address="0x824627930c62aF8e8622cAd17Def8cB122290643",
            leaf=0,
            private_key="0x987",
            mnemonic="alter phrase erupt aun glory media want aun noble tooth fine aun",
        ),
        Wallet(
            address="0xfd267dd115C1e486369D3A5ddF26B8c12f16FdDA",
            leaf=1,
            private_key="0x876",
            mnemonic="aun aun aun aun v aun aun aun aun aun aun aun",
        ),
        Wallet(
            address="0x0af880Ed1dF24Cd35BCA3c9fbD45A5586200e7Cb",
            leaf=0,
            private_key="0x765",
            mnemonic="fine fine fine fine fine fine fine fine fine fine fine fine",
        ),
    ]
    async with session() as s:
        async with s.begin():
            s.add_all(data)
    return data
