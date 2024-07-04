from fastapi import *
from fastapi.security import OAuth2PasswordBearer
from model.booking import BookingModel, Success, Error, BookingInfo, Data


BookingRouter = APIRouter()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/api/user/auth")


@BookingRouter.post(
	"/api/booking",
	response_model = Success,
	responses={
		200: {"model": Success, "description": "建立成功"},
		400: {"model": Error, "description": "建立失敗，輸入不正確或其他原因"},
		403: {"model": Error, "description": "未登入系統，拒絕存取"},
		500: {"model": Error, "description": "伺服器內部錯誤"}
	}
)
async def booking(bookingInfo:BookingInfo, token: str = Depends(oauth2_scheme)):
    result = await BookingModel.booking(bookingInfo, token)
    return result


@BookingRouter.get(
	"/api/booking",
	response_model = Data,
	responses={
		200: {"model": Data, "description": "尚未確認下單的預定行程資料，null 表示沒有資料"},
		403: {"model": Error, "description": "未登入系統，拒絕存取"},
	}
)
async def get_booking(token: str = Depends(oauth2_scheme)):
    result = await BookingModel.get_booking(token)
    return result


@BookingRouter.delete(
    "/api/booking",
	response_model = Success,
	responses={
		200: {"model": Success, "description": "刪除成功"},
		403: {"model": Error, "description": "未登入系統，拒絕存取"},
	}
)
async def delete_booking(token: str = Depends(oauth2_scheme)):
    result = await BookingModel.delete_booking(token)
    return result