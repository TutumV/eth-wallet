from typing import Optional

from _decimal import Decimal
from eth44.crypto import HDKey as HDKeyEthereum
from eth44.crypto import HDPrivateKey
from eth_utils.units import units
from mnemonic import Mnemonic
from sqlalchemy import select
from web3 import AsyncHTTPProvider, AsyncWeb3

from app.config import settings
from app.core.database import async_session
from app.core.exception import AddressNotValidException, WalletNotFoundException
from app.model import Wallet
from app.schemas import WalletCreate, WalletDetail, WalletWithBalance


class WalletController:
    HD_PATH = "m/44'/60'/0'"
    DEFAULT_ACCOUNT = 0

    @classmethod
    async def _get_provider(cls) -> AsyncWeb3:
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

    @classmethod
    async def _get_root_key(cls, mnemonic) -> list:
        master_key = HDPrivateKey.master_key_from_mnemonic(mnemonic=mnemonic)
        return HDKeyEthereum.from_path(master_key, cls.HD_PATH)

    @classmethod
    async def _generate_wallet_data(cls, root_key, mnemonic, leaf=0) -> dict:
        w3 = await cls._get_provider()
        keys = HDKeyEthereum.from_path(
            root_key=root_key, path='{account}/{leaf}'.format(account=cls.DEFAULT_ACCOUNT, leaf=leaf)
        )
        private_key = keys[-1]
        address = private_key.public_key.address()
        checksum_address = w3.to_checksum_address(address)
        data = {
            "address": checksum_address,
            "private_key": private_key._key.to_hex(),
            "leaf": leaf,
            "mnemonic": mnemonic,
        }
        return data

    @classmethod
    async def create(cls, data: WalletCreate) -> WalletDetail:
        if data.mnemonic:
            mnemonic = data.mnemonic
            leaf = await cls._get_next_leaf(mnemonic=data.mnemonic)
        else:
            mnemonic = await cls._generate_mnemonic()
            leaf = 0

        root_keys = await cls._get_root_key(mnemonic=mnemonic)
        wallet = await cls._generate_wallet_data(root_key=root_keys[-1], mnemonic=mnemonic, leaf=leaf)

        async with async_session() as session:
            async with session.begin():
                session.add(Wallet(**wallet))
        return WalletDetail(**wallet)

    @classmethod
    async def _validate_address(cls, address) -> None:
        w3 = await cls._get_provider()
        if not w3.is_address(address):
            raise AddressNotValidException()

    @classmethod
    async def _get_balance(cls, address) -> Optional[int]:
        w3 = await cls._get_provider()
        if await w3.is_connected() is False:
            balance = None
        else:
            balance = await w3.eth.get_balance(address)
        return balance

    @classmethod
    async def _wei_to_ether(cls, wei) -> Decimal:
        """
        this method don't use w3.from_wei because it return Union[int, Decimal)
        """
        ether = wei / units.get('ether')
        return Decimal(value=ether)

    @classmethod
    async def get_wallet_with_balance(cls, address):
        """
        validate the address
        get an account
        get the balance in wei, then convert it to ether
        """
        await cls._validate_address(address=address)

        async with async_session() as session:
            result = await session.execute(select(Wallet).filter(Wallet.address == address))
            wallet = result.scalar_one_or_none()
            if wallet is None:
                raise WalletNotFoundException()

        balance = await cls._get_balance(address)
        balance = await cls._wei_to_ether(balance) if balance else balance
        return WalletWithBalance(
            address=wallet.address,
            private_key=wallet.private_key,
            mnemonic=wallet.mnemonic,
            leaf=wallet.leaf,
            balance=balance,
        )
