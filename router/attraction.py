from fastapi import *
from model.attraction import AttractionModel,SearchAttractionsData,Data,Error


AttractionRouter = APIRouter()


@AttractionRouter.get(	
    "/api/attractions",
	response_model = SearchAttractionsData,
	responses={
		200: {"model": SearchAttractionsData, "description": "正常運作"},
		500: {"model": Error, "description": "伺服器內部錯誤"}
    }
)
async def search_attractions_data( 
    page:int = Query(..., ge=0, description="要取得的分頁，每頁 12 筆資料"), 
    keyword:str = Query(None, description="用來完全比對捷運站名稱、或模糊比對景點名稱的關鍵字，沒有給定則不做篩選")
):
    result = await AttractionModel.search_attractions_data(page, keyword)
    return result


@AttractionRouter.get(
    "/api/attraction/{attractionId}",
    response_model = Data,    
	responses={
    	200: {"model": Data, "description": "景點資料"},
        400: {"model": Error, "description": "景點編號不正確"},
        500: {"model": Error, "description": "伺服器內部錯誤"} 
	}
)
async def read_attractionId(attractionId: int):
    result = await AttractionModel.read_attractionId(attractionId)
    return result