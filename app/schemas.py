from typing import List, Optional

from _decimal import Decimal
from pydantic import BaseModel, RootModel, computed_field

from app.config import settings


class WalletDetail(BaseModel):
    address: str
    private_key: str
    mnemonic: str
    leaf: int

    @computed_field
    def explorer_url(self) -> str:
        return settings.explorer_url.format(address=self.address)


class WalletWithBalance(WalletDetail):
    balance: Optional[Decimal]


class WalletCreate(BaseModel):
    mnemonic: Optional[str] = None


class WalletList(RootModel):
    root: List[WalletDetail]


class Message(BaseModel):
    detail: str
