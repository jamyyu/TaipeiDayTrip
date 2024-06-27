from sqlite3 import Date
from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
import os 
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
import mysql.connector 
from mysql.connector import pooling
from pydantic import BaseModel, EmailStr 
from typing import Union
import json
import bcrypt
import jwt
from datetime import date, datetime, timedelta

app = FastAPI()


app.mount("/static", StaticFiles(directory = "static"), name = "static")


load_dotenv()
mypassword = os.getenv("mypassword")
key = os.getenv("mykey")

pool = pooling.MySQLConnectionPool(
	pool_name = "mypool",
	pool_size = 10,  
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


class Success(BaseModel):
	ok: bool
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
class Data(BaseModel):
	data: Union [list, dict, str, Attraction]
class SearchAttractionsData(BaseModel):
	nextPage: Union [int, None] = None
	data: Union [Attraction, list, None] = []
class UserSignup(BaseModel):
	name:str
	email:EmailStr
	password:str
class UserSignin(BaseModel):
	email:str
	password:str
class Token(BaseModel):
	token: str
class BookingInfo(BaseModel):
	attractionId:int
	date:Date
	time:str
	price:int


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
    page:int = Query(..., ge=0, description="要取得的分頁，每頁 12 筆資料"), 
    keyword:str = Query(None, description="用來完全比對捷運站名稱、或模糊比對景點名稱的關鍵字，沒有給定則不做篩選")
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
			ORDER BY category.name DESC
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
			ORDER BY category.name DESC
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
    response_model = Data,    
	responses={
    	200: {"model": Data, "description": "景點資料"},
        400: {"model": Error, "description": "景點編號不正確"},
        500: {"model": Error, "description": "伺服器內部錯誤"} 
	}
)
async def read_attractionId(attractionId: int):
	query = """SELECT spot.id, spot.name, category.name AS category, spot.description, spot.address, spot.transport, mrt.name AS mrt, spot.lat, spot.lng, spot.images 
    FROM spot INNER JOIN mrt ON spot.id = mrt.spot_id 
    INNER JOIN category ON spot.id = category.spot_id 
    WHERE spot.id = %s"""
	data = execute_query(query, (attractionId,), dictionary = True)
	if not data:
		return JSONResponse(content = {"error": True, "message": "Attraction not found"}, status_code = 400)
	if "images" in data[0]:
		data[0]["images"] = json.loads(data[0]["images"])
		return Data(data = Attraction(**data[0]))


@app.get(
    "/api/mrts",
    response_model = Data, 
    responses={
    	200: {"model": Data, "description": "正常運作"},
        500: {"model": Error, "description": "伺服器內部錯誤"} 
	}
)
async def mrt_list():
	query = "SELECT name FROM mrt GROUP BY name ORDER BY COUNT(name) DESC"
	data = execute_query(query)
	newData = []
	for mrt in data:
		if mrt[0] != None:
			newData.append(mrt[0])
	return Data(data = newData)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt() #生成一個新的隨機鹽值
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


@app.post(
	"/api/user",
	response_model = Success,
	responses={
    	200: {"model": Success, "description": "註冊成功"},
		400: {"model": Error, "description": "註冊失敗，重複的 Email 或其他原因"},
        500: {"model": Error, "description": "伺服器內部錯誤"} 
	}
)
async def signup(user: UserSignup):
	query = "SELECT email FROM user WHERE email=%s"
	name = user.name
	email = user.email
	password =user.password
	data = execute_query(query, (email,), dictionary = True)
	if data:
		return JSONResponse(content = {"error": True, "message": "Email already registered"}, status_code = 400)
	else:
		hashed_password = hash_password(password)
		query = "INSERT INTO user (name, email, password) VALUES (%s, %s, %s)"
		execute_query(query, (name, email, hashed_password))
		return Success(ok = True)


@app.put(
	"/api/user/auth",
	response_model = Token,
	responses={
    	200: {"model": Token, "description": "登入成功，取得有效期為七天的 JWT 加密字串"},
		400: {"model": Error, "description": "登入失敗，帳號或密碼錯誤或其他原因"},
        500: {"model": Error, "description": "伺服器內部錯誤"} 
	}
)
async def signin(user: UserSignin):
	email = user.email
	password = user.password
	query = "SELECT id, name, email, password FROM user WHERE email = %s"
	data = execute_query(query, (email,), dictionary = True)
	if not data or not verify_password(password, data[0]["password"]):
		return JSONResponse(content = {"error": True, "message": "Invalid email or password"}, status_code = 400)
	else:
		now = datetime.now()
		expiration = now + timedelta(days = 7)
		exp_timestamp = int(expiration.timestamp())
		payload = {
    	"id": data[0]["id"],
   		"name": data[0]["name"],
    	"email": data[0]["email"],
    	"exp": exp_timestamp  # 添加過期時間
		}
		encoded = jwt.encode(payload, key, algorithm = "HS256")
		#print(encoded)
		return Token(token = encoded)
	

oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/api/user/auth")


@app.get(
	"/api/user/auth",
	response_model = Data,
	responses={
    	200: {"model": Data, "description": "已登入的會員資料，null 表示未登入"},
	}
)
async def check_auth(token: str = Depends(oauth2_scheme)):
	try:
		payload = jwt.decode(token, key, algorithms = "HS256")
		return Data(data = {"id": payload["id"], "name": payload["name"], "email": payload["email"]})
	except:
		return Data(data = "null")


@app.post(
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
	attractionId = bookingInfo.attractionId
	bookingDate = bookingInfo.date
	bookingTime = bookingInfo.time
	bookingPrice = bookingInfo.price
	# 驗證 JWT 並獲取 user_id
	try:
		payload = jwt.decode(token, key, algorithms = "HS256")
		user_id = payload["id"]
	except:
		return JSONResponse(content = {"error": True, "message": "Not logged in, access denied"}, status_code = 403)
	# 檢查景點是否存在
	query = "SELECT id FROM spot WHERE id = %s"
	data = execute_query(query, (attractionId,), dictionary = True)
	if not data:
		return JSONResponse(content = {"error": True, "message": "Attraction not found"}, status_code = 400)
	# 檢查日期是否在明日之後
	if bookingDate <= date.today():
		return JSONResponse(content = {"error": True, "message": "Date must be after today"}, status_code = 400)
	# 檢查時間是否正確
	if bookingTime != "morning" and bookingTime != "afternoon":
		return JSONResponse(content = {"error": True, "message": "Time must be morning or afternoon"}, status_code = 400)
	# 檢查時間與價格是否搭配
	if (bookingTime == "morning" and bookingPrice != 2000) or (bookingTime == "afternoon" and bookingPrice != 2500):
		return JSONResponse(content = {"error": True, "message": "Price must be 2000 for morning and 2500 for afternoon"}, status_code = 400)
	# 預定資料寫入資料庫
	query = "SELECT id FROM booking WHERE user_id = %s"
	bookingData = execute_query(query, (user_id,))
	if not bookingData:
		query = "INSERT INTO booking (user_id, spot_id, date, time, price) VALUES (%s, %s, %s, %s, %s)"
		execute_query(query, (user_id, attractionId, bookingDate, bookingTime, bookingPrice))
	else:
		query = "UPDATE booking SET spot_id = %s, date = %s, time = %s, price = %s WHERE user_id = %s"
		execute_query(query, (attractionId, bookingDate, bookingTime, bookingPrice, user_id))
	return Success(ok = True)


@app.get(
	"/api/booking",
	response_model = Data,
	responses={
		200: {"model": Data, "description": "尚未確認下單的預定行程資料，null 表示沒有資料"},
		403: {"model": Error, "description": "未登入系統，拒絕存取"},
	}
)
async def get_booking(token: str = Depends(oauth2_scheme)):
	try:
		payload = jwt.decode(token, key, algorithms = "HS256")
		user_id = payload["id"]
	except:
		return JSONResponse(content = {"error": True, "message": "Not logged in, access denied"}, status_code = 403)
	query = "SELECT * FROM booking WHERE user_id = %s"
	bookingData = execute_query(query, (user_id,), dictionary=True)
	if bookingData:
		bookingData = bookingData[0]
		spot_id = bookingData["spot_id"]
		query = "SELECT name, address, images FROM spot WHERE id = %s"
		attractionData = execute_query(query, (spot_id,), dictionary=True)
		attractionData = attractionData[0]
		if "images" in attractionData:
			attractionData["images"] = json.loads(attractionData["images"])
		return Data(data = {"attraction":{"id": spot_id, "name": attractionData["name"], "address": attractionData["address"], "image":attractionData["images"][0]}, 
						"date": bookingData["date"].isoformat(), "time": bookingData["time"], "price": bookingData["price"]})
	else:
		return Data(data = "null")


@app.delete(
    "/api/booking",
	response_model = Success,
	responses={
		200: {"model": Success, "description": "刪除成功"},
		403: {"model": Error, "description": "未登入系統，拒絕存取"},
	}
)
async def delete_booking(token: str = Depends(oauth2_scheme)):
	try:
		payload = jwt.decode(token, key, algorithms = "HS256")
		user_id = payload["id"]
	except:
		return JSONResponse(content = {"error": True, "message": "Not logged in, access denied"}, status_code = 403)
	query = "SELECT * FROM booking WHERE user_id = %s"
	bookingData = execute_query(query, (user_id,), dictionary=True)
	if bookingData:
		query = "DELETE FROM booking WHERE user_id = %s"
		execute_query(query, (user_id,))
	return Success(ok = True)