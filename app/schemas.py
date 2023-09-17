from typing import List, Optional

from _decimal import Decimal
from pydantic import BaseModel, ConfigDict, RootModel, computed_field, field_validator

from app.config import settings


class WalletDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    address: str
    private_key: str
    mnemonic: str
    leaf: int

    @computed_field
    def explorer_url(self) -> str:
        return settings.explorer_address_url.format(address=self.address)


class WalletWithBalance(WalletDetail):
    balance: Decimal

    @field_validator("balance")
    @classmethod
    def validate_balance(cls, value) -> str:
        return f'{value:.18f}'


class WalletCreate(BaseModel):
    mnemonic: Optional[str] = None


class WalletSend(BaseModel):
    to: str
    amount: Decimal


class WalletSendResult(BaseModel):
    transaction_id: str

    @computed_field
    def explorer_url(self) -> str:
        return settings.explorer_transaction_url.format(tx_id=self.transaction_id)


class WalletList(RootModel):
    root: List[WalletDetail]


class Message(BaseModel):
    detail: str
