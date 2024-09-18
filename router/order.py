from fastapi import APIRouter, Depends
from model.order import OrderModel, Data, Error, OrderInfo
from fastapi.security import OAuth2PasswordBearer

OrderRouter = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/auth")


@OrderRouter.post(
    "/api/orders",
    response_model=Data,
    responses={
        200: {"model": Data, "description": "訂單建立成功，包含付款狀態 ( 可能成功或失敗 )"},
        400: {"model": Error, "description": "訂單建立失敗，輸入不正確或其他原因"},
        403: {"model": Error, "description": "未登入系統，拒絕存取"},
        500: {"model": Error, "description": "伺服器內部錯誤"}
    }
)
async def order(orderInfo: OrderInfo, token: str = Depends(oauth2_scheme)):
    result = await OrderModel.order(orderInfo, token)
    return result


@OrderRouter.get(
    "/api/orders/{order_number}",
    response_model=Data,
    responses={
        200: {"model": Data, "description": "尚未確認下單的預定行程資料，null 表示沒有資料"},
        403: {"model": Error, "description": "未登入系統，拒絕存取"},
    }
)
async def get_order(order_number: str, token: str = Depends(oauth2_scheme)):
    result = await OrderModel.get_order(order_number, token)
    return result