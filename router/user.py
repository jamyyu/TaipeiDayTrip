from fastapi import *
from model.user import UserModel, Success, Error, UserSignup, Token, UserSignin, Data
from fastapi.security import OAuth2PasswordBearer 


UserRouter = APIRouter()


@UserRouter.post(
	"/api/user",
	response_model = Success,
	responses={
    	200: {"model": Success, "description": "註冊成功"},
		400: {"model": Error, "description": "註冊失敗，重複的 Email 或其他原因"},
        500: {"model": Error, "description": "伺服器內部錯誤"} 
	}
)
async def signup(user: UserSignup):
    result = await UserModel.signup(user)
    return result

@UserRouter.put(
	"/api/user/auth",
	response_model = Token,
	responses={
    	200: {"model": Token, "description": "登入成功，取得有效期為七天的 JWT 加密字串"},
		400: {"model": Error, "description": "登入失敗，帳號或密碼錯誤或其他原因"},
        500: {"model": Error, "description": "伺服器內部錯誤"} 
	}
)
async def signin(user: UserSignin):
    result = await UserModel.signin(user)
    return result


oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/api/user/auth")

@UserRouter.get(
	"/api/user/auth",
	response_model = Data,
	responses={
    	200: {"model": Data, "description": "已登入的會員資料，null 表示未登入"},
	}
)
async def check_auth(token: str = Depends(oauth2_scheme)):
    result = await UserModel.check_auth(token)
    return result