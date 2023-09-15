from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.controller import WalletController
from app.core.database import async_session
from app.core.exception import AddressNotValidException, WalletNotFoundException
from app.model import Wallet
from app.schemas import (
    Message,
    WalletCreate,
    WalletDetail,
    WalletList,
    WalletWithBalance,
)

router = APIRouter()


@router.post('/create_wallet', status_code=201)
async def create_wallet_view(data: WalletCreate) -> WalletDetail:
    return await WalletController.create(data=data)


@router.get('/wallets')
async def wallets_view(limit: int = 20, offset: int = 0) -> WalletList:
    async with async_session() as session:
        result = await session.execute(select(Wallet).order_by(Wallet.id).limit(limit).offset(offset))
        return WalletList(root=[WalletDetail(**wallet.__dict__) for wallet in result.scalars().all()])


@router.get(
    "/wallet/{address}", responses={200: {"model": WalletWithBalance}, 400: {"model": Message}, 404: {"model": Message}}
)
async def wallet_detail_view(address) -> WalletWithBalance:
    try:
        return await WalletController.get_wallet_with_balance(address=address)
    except AddressNotValidException:
        raise HTTPException(status_code=400, detail="Address Not Valid")
    except WalletNotFoundException:
        raise HTTPException(status_code=404, detail="Wallet Not Found")
