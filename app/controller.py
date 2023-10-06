from typing import Optional

from _decimal import Decimal
from aiohttp import ClientResponseError
from eth44.tools import Wallet as WalletData
from eth44.tools import create_wallet
from eth_utils.units import units
from mnemonic import Mnemonic
from sqlalchemy import select
from web3 import AsyncHTTPProvider, AsyncWeb3

from app.config import settings
from app.core.database import async_session
from app.core.exception import (
    AddressNotValidException,
    InsufficientFundsException,
    NodeException,
    TargetWalletNotValidException,
    WalletNotFoundException,
)
from app.model import Wallet
from app.schemas import (
    WalletCreate,
    WalletDetail,
    WalletSend,
    WalletSendResult,
    WalletWithBalance,
)


class WalletController:
    HD_PATH = "m/44'/60'/0'"
    DEFAULT_ACCOUNT = 0

    def __init__(self):
        self.w3 = self._get_provider()

    @classmethod
    def _get_provider(cls) -> AsyncWeb3:
        provider = AsyncHTTPProvider(settings.node_url)
        return AsyncWeb3(provider=provider)

    @classmethod
    async def _generate_mnemonic(cls) -> str:
        return Mnemonic('english').generate()

    @classmethod
    async def _get_next_leaf(cls, mnemonic: str) -> int:
        async with async_session() as session:
            result = await session.execute(
                select(Wallet).filter(Wallet.mnemonic == mnemonic).order_by(Wallet.id.desc()).limit(1)
            )
            wallet = result.scalar_one_or_none()
            return wallet.leaf + 1 if wallet else 0

    async def _generate_wallet_data(self, mnemonic, leaf=0) -> WalletData:
        wallet: WalletData = create_wallet(mnemonic=mnemonic, leaf=leaf)
        wallet.address = self.w3.to_checksum_address(wallet.address)
        return wallet

    async def create(self, data: WalletCreate) -> WalletDetail:
        if data.mnemonic:
            mnemonic = data.mnemonic
            leaf = await self._get_next_leaf(mnemonic=data.mnemonic)
        else:
            mnemonic = await self._generate_mnemonic()
            leaf = 0

        wallet = await self._generate_wallet_data(mnemonic=mnemonic, leaf=leaf)

        async with async_session() as session:
            async with session.begin():
                session.add(
                    Wallet(
                        address=wallet.address,
                        leaf=wallet.leaf,
                        mnemonic=wallet.mnemonic,
                        private_key=wallet.private_key,
                    )
                )
        return WalletDetail(
            address=wallet.address, private_key=wallet.private_key, mnemonic=wallet.mnemonic, leaf=wallet.leaf
        )

    async def _address_is_valid(self, address) -> bool:
        return self.w3.is_address(address)

    async def _get_balance(self, address) -> Optional[int]:
        try:
            return await self.w3.eth.get_balance(address)
        except ClientResponseError:
            raise NodeException()

    @classmethod
    async def _wei_to_ether(cls, wei) -> Decimal:
        """
        this method don't use w3.from_wei because it return Union[int, Decimal)
        """
        ether = wei / units.get('ether')
        return Decimal(ether)

    @classmethod
    async def _get_wallet(cls, address):
        async with async_session() as session:
            result = await session.execute(select(Wallet).filter(Wallet.address == address))
            return result.scalar_one_or_none()

    async def get_wallet_with_balance(self, address):
        """
        validate the address
        get an account
        get the balance in wei, then convert it to ether
        """
        is_valid = await self._address_is_valid(address=address)
        if not is_valid:
            raise AddressNotValidException()

        wallet = await self._get_wallet(address)
        if not wallet:
            raise WalletNotFoundException()

        wei_balance = await self._get_balance(address)
        ether_balance = await self._wei_to_ether(wei_balance)
        return WalletWithBalance(
            address=wallet.address,
            private_key=wallet.private_key,
            mnemonic=wallet.mnemonic,
            leaf=wallet.leaf,
            balance=ether_balance,
        )

    async def _gas_price(self):
        try:
            return await self.w3.eth.gas_price
        except ClientResponseError:
            raise NodeException()

    async def _gas_count(self, from_, to_, amount):
        try:
            return await self.w3.eth.estimate_gas({'to': to_, 'from': from_, 'value': amount})
        except ClientResponseError:
            raise NodeException()

    async def _send_raw_transaction(self, from_, to_, amount, private_key, gas, gas_price):
        try:
            nonce = await self.w3.eth.get_transaction_count(from_)
            signed_txn = self.w3.eth.account.sign_transaction(
                dict(
                    nonce=nonce,
                    gas=gas,
                    gasPrice=gas_price,
                    to=to_,
                    value=amount,
                    data=b'',
                    chainId=settings.chain_id,
                ),
                private_key=private_key,
            )
            result = await self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            return result.hex()
        except (ClientResponseError, ValueError):
            raise NodeException()

    async def send(self, address, data: WalletSend):
        # validate from_ to_ addresses
        from_is_valid = await self._address_is_valid(address=address)
        if not from_is_valid:
            raise AddressNotValidException()
        to_is_valid = await self._address_is_valid(address=data.to)
        if not to_is_valid:
            raise TargetWalletNotValidException()
        # get wallet data
        wallet = await self._get_wallet(address)
        if not wallet:
            raise WalletNotFoundException()
        # get balance
        wei_balance = await self._get_balance(address)
        ether_balance = await self._wei_to_ether(wei_balance)
        # calculate fee
        amount = self.w3.to_wei(data.amount, 'ether')
        gas_count = await self._gas_count(from_=address, to_=data.to, amount=amount)
        gas_price = await self._gas_price()
        wei_fee = gas_count * gas_price
        ether_fee = await self._wei_to_ether(wei_fee)
        # check balance
        if wei_balance < (amount + wei_fee):
            raise InsufficientFundsException(
                available=ether_balance,
                required=ether_fee + data.amount,
            )
        # create and send raw tx
        tx_id = await self._send_raw_transaction(
            from_=address,
            to_=data.to,
            gas=gas_count,
            gas_price=gas_price,
            amount=amount,
            private_key=wallet.private_key,
        )
        return WalletSendResult(transaction_id=tx_id)
