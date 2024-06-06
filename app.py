from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
import os
from fastapi.staticfiles import StaticFiles
import mysql.connector
from mysql.connector import pooling
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Union
import json

app=FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")


load_dotenv()
mypassword = os.getenv("mypassword")

pool = pooling.MySQLConnectionPool(
	pool_name = "mypool",
	pool_size = 5,  
	pool_reset_session = True,
	host = "localhost",
	database = "TaipeiDayTrip",
	user = "root",
	password = mypassword,
)

def execute_query(query, params = None, dictionary = False):
    try:
        cnx = pool.get_connection()
        if cnx.is_connected():
            cursor = cnx.cursor(dictionary = dictionary)
            cursor.execute(query, params)
            if query.strip().lower().startswith("select"):
                data = cursor.fetchall()
                return data
            else:
                cnx.commit()
    except mysql.connector.Error as error:
        print("Error while connecting to MySQL", error)
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()


class Error(BaseModel):
	error: bool
	message: str
class Attraction(BaseModel):
	id: int
	name: str
	category: str
	description: str
	address: str
	transport: str
	mrt: Union[str, None] = None
	lat: float
	lng: float
	images: list[str]
class AttractionData(BaseModel):
	data: Attraction
class Data(BaseModel):
	data: Union [list, dict]
class SearchAttractionsData(BaseModel):
	nextPage: Union [int, None] = None
	data: Union [Attraction, list, None] = []


# Static Pages (Never Modify Code in this Block)
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@app.get("/attraction/{id}", include_in_schema=False)
async def attraction(request: Request, id: int):
	return FileResponse("./static/attraction.html", media_type="text/html")
@app.get("/booking", include_in_schema=False)
async def booking(request: Request):
	return FileResponse("./static/booking.html", media_type="text/html")
@app.get("/thankyou", include_in_schema=False)
async def thankyou(request: Request):
	return FileResponse("./static/thankyou.html", media_type="text/html")


@app.exception_handler(Exception)
async def custom_500_handler(request: Request, exc: Exception):
	return JSONResponse(content = {"error": True, "message": "Internal Server Error"}, status_code = 500)


@app.get(
	"/api/attractions",
	response_model = SearchAttractionsData,
	responses={
		200: {"model": SearchAttractionsData, "description": "正常運作"},
		500: {"model": Error, "description": "伺服器內部錯誤"}
	}
)
async def search_attractions_data(
    request: Request, 
    page:int = Query(..., ge=0, description="要取得的分頁，每頁 12 筆資料"), 
    keyword: str = Query(None, description="用來完全比對捷運站名稱、或模糊比對景點名稱的關鍵字，沒有給定則不做篩選")
):
	limit = 12
	offset = page*limit
	nextPage = page+1
	if not keyword:
		query = """SELECT spot.id, spot.name, category.name AS category, spot.description, spot.address, spot.transport, mrt.name AS mrt, spot.lat, spot.lng, spot.images 
		FROM spot INNER JOIN mrt ON spot.id = mrt.spot_id 
		INNER JOIN category ON spot.id = category.spot_id
		INNER JOIN (
			SELECT name, COUNT(name) AS category_count
			FROM category
			GROUP BY name
		) AS CategoryCounts ON category.name = CategoryCounts.name
		ORDER BY CategoryCounts.category_count DESC, spot.id ASC
		LIMIT %s OFFSET %s"""
		data = execute_query(query, params = (limit+1, offset), dictionary = True)
	else:
		query = "SELECT name FROM mrt GROUP BY name ORDER BY COUNT(name) DESC"
		data = execute_query(query, params = None, dictionary = True)
		mrt_list=[]
		for d in data:
			mrt_list.append(d["name"])
		if keyword in mrt_list:
			query = """SELECT spot.id, spot.name, category.name AS category, spot.description, spot.address, spot.transport, mrt.name AS mrt, spot.lat, spot.lng, spot.images 
			FROM spot INNER JOIN mrt ON spot.id = mrt.spot_id 
			INNER JOIN category ON spot.id = category.spot_id
			WHERE mrt.name = %s
			ORDER BY spot.id ASC
			LIMIT %s OFFSET %s"""
			data = execute_query(query, params = (keyword, limit+1, offset), dictionary = True)
		else:
			limit = 12
			offset = page*limit
			nextPage = page+1
			query = """SELECT spot.id, spot.name, category.name AS category, spot.description, spot.address, spot.transport, mrt.name AS mrt, spot.lat, spot.lng, spot.images 
			FROM spot INNER JOIN mrt ON spot.id = mrt.spot_id 
			INNER JOIN category ON spot.id = category.spot_id
			WHERE spot.name LIKE %s
			ORDER BY spot.id ASC
			LIMIT %s OFFSET %s"""
			data = execute_query(query, params = (f"%{keyword}%", limit+1, offset), dictionary = True)
	if data is None:
		return SearchAttractionsData(nextPage = None, data = [])
	attractions_list = []
	for attraction in data[:limit]:
		if "images" in attraction:
			attraction["images"] = json.loads(attraction["images"])
			attractions_list.append(Attraction(**attraction))
	if len(data) <= limit:
		nextPage = None
	return SearchAttractionsData(nextPage = nextPage, data = attractions_list)


@app.get(
    "/api/attraction/{attractionId}",
    response_model = AttractionData,    
	responses={
    	200: {"model": AttractionData, "description": "景點資料"},
        400: {"model": Error, "description": "景點編號不正確"},
        500: {"model": Error, "description": "伺服器內部錯誤"} 
	}
)
async def read_attractionId(request: Request, attractionId: int):
	query = """SELECT spot.id, spot.name, category.name AS category, spot.description, spot.address, spot.transport, mrt.name AS mrt, spot.lat, spot.lng, spot.images 
    FROM spot INNER JOIN mrt ON spot.id = mrt.spot_id 
    INNER JOIN category ON spot.id = category.spot_id 
    WHERE spot.id = %s"""
	data = execute_query(query, (attractionId,), dictionary = True)
	if not data:
		return JSONResponse(content = {"error": True, "message": "Attraction not found"}, status_code = 400)
	if "images" in data[0]:
		data[0]["images"] = json.loads(data[0]["images"])
		return AttractionData(data = Attraction(**data[0]))


@app.get(
    "/api/mrts",
    response_model = Data, 
    responses={
    	200: {"model": Data, "description": "正常運作"},
        500: {"model": Error, "description": "伺服器內部錯誤"} 
	}
)
async def mrt_list(request: Request):
	query = "SELECT name FROM mrt GROUP BY name ORDER BY COUNT(name) DESC"
	data = execute_query(query)
	newData = []
	for mrt in data:
		if mrt[0] != None:
			newData.append(mrt[0])
	return Data(data = newData)

