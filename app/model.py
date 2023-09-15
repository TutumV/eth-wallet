from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Wallet(Base):
    __tablename__ = "wallet"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(index=True)
    leaf: Mapped[int]
    mnemonic: Mapped[str]
    private_key: Mapped[str]
