from fastapi import *
from model.mrt import MRTModel, Data, Error


MRTRouter = APIRouter()


@MRTRouter.get(
    "/api/mrts",
    response_model = Data, 
    responses={
    	200: {"model": Data, "description": "正常運作"},
        500: {"model": Error, "description": "伺服器內部錯誤"} 
	}
)
async def mrt_list():
    result = await MRTModel.mrt_list()
    return result