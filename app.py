import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import random
import re
from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
import os 
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
import mysql.connector 
from mysql.connector import pooling
from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal, Union
import json
import bcrypt
import jwt
from datetime import date, datetime, timedelta
import urllib.request as req

app = FastAPI()


app.mount("/static", StaticFiles(directory = "static"), name = "static")


load_dotenv()
mypassword = os.getenv("mypassword")
key = os.getenv("mykey")
partner_key = os.getenv("partner_key")

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
	name: str
	email: EmailStr
	password: str
class UserSignin(BaseModel):
	email: str
	password: str
class Token(BaseModel):
	token: str
class BookingInfo(BaseModel):
	attractionId: int
	date: date
	time: Literal["morning", "afternoon"]
	price: int

	@field_validator("date")
	def date_must_be_in_the_future(bookingDate):
		if bookingDate <= date.today():
			raise ValueError("Date must be after today")
		return bookingDate
	
class AttractionInfo(BaseModel):
	id: int
	name: str
	address: str
	image: str
class Trip(BaseModel):
	attraction: AttractionInfo
	date: date
	time: Literal["morning", "afternoon"]

	@field_validator("date")
	def date_must_be_in_the_future(bookingDate):
		if bookingDate <= date.today():
			raise ValueError("Date must be after today")
		return bookingDate

class Contact(BaseModel):
	name: str
	email:EmailStr
	phone: str
	
	@field_validator("phone")
	def validate_phone(phone):
		phone_pattern = re.compile(r"^09\d{8}$")
		if not phone_pattern.match(phone):
			raise ValueError("Invalid phone number format")
		return phone

class Order(BaseModel):
	price:int
	trip: Trip
	contact: Contact
class OrderInfo(BaseModel):
	prime: str
	order: Order


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
	new_data = []
	for mrt in data:
		if mrt[0] != None:
			new_data.append(mrt[0])
	return Data(data = new_data)


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
	attraction_id = bookingInfo.attractionId
	booking_date = bookingInfo.date
	booking_time = bookingInfo.time
	booking_price = bookingInfo.price
	# 驗證 JWT 並獲取 user_id
	try:
		payload = jwt.decode(token, key, algorithms = "HS256")
		user_id = payload["id"]
	except:
		return JSONResponse(content = {"error": True, "message": "Not logged in, access denied"}, status_code = 403)
	# 檢查景點是否存在
	query = "SELECT id FROM spot WHERE id = %s"
	data = execute_query(query, (attraction_id,), dictionary = True)
	if not data:
		return JSONResponse(content = {"error": True, "message": "Attraction not found"}, status_code = 400)
	# 檢查時間與價格是否搭配
	if (booking_time == "morning" and booking_price != 2000) or (booking_time == "afternoon" and booking_price != 2500):
		return JSONResponse(content = {"error": True, "message": "Price must be 2000 for morning and 2500 for afternoon"}, status_code = 400)
	# 預定資料寫入資料庫
	query = "SELECT id FROM booking WHERE user_id = %s"
	bookingData = execute_query(query, (user_id,))
	if not bookingData:
		query = "INSERT INTO booking (user_id, spot_id, date, time, price) VALUES (%s, %s, %s, %s, %s)"
		execute_query(query, (user_id, attraction_id, booking_date, booking_time, booking_price))
	else:
		query = "UPDATE booking SET spot_id = %s, date = %s, time = %s, price = %s WHERE user_id = %s"
		execute_query(query, (attraction_id, booking_date, booking_time, booking_price, user_id))
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
	booking_data = execute_query(query, (user_id,), dictionary=True)
	if booking_data:
		booking_data = booking_data[0]
		spot_id = booking_data["spot_id"]
		query = "SELECT name, address, images FROM spot WHERE id = %s"
		attraction_data = execute_query(query, (spot_id,), dictionary=True)
		attraction_data = attraction_data[0]
		if "images" in attraction_data:
			attraction_data["images"] = json.loads(attraction_data["images"])
		return Data(data = {"attraction":{"id": spot_id, "name": attraction_data["name"], "address": attraction_data["address"], "image":attraction_data["images"][0]}, 
						"date": booking_data["date"].isoformat(), "time": booking_data["time"], "price": booking_data["price"]})
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
	booking_data = execute_query(query, (user_id,), dictionary=True)
	if booking_data:
		query = "DELETE FROM booking WHERE user_id = %s"
		execute_query(query, (user_id,))
	return Success(ok = True)


@app.post(
	"/api/orders",
	response_model = Data,
	responses={
		200: {"model": Data, "description": "訂單建立成功，包含付款狀態 ( 可能成功或失敗 )"},
		400: {"model": Error, "description": "訂單建立失敗，輸入不正確或其他原因"},
		403: {"model": Error, "description": "未登入系統，拒絕存取"},
		500: {"model": Error, "description": "伺服器內部錯誤"}
	}
)
async def order(orderInfo: OrderInfo, token: str = Depends(oauth2_scheme)):
	# 驗證 JWT 並獲取 user_id
	try:
		payload = jwt.decode(token, key, algorithms = "HS256")
		user_id = payload["id"]
	except:
		return JSONResponse(content = {"error": True, "message": "Not logged in, access denied"}, status_code = 403)

	timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
	random_number = ''.join(random.choices('0123456789', k=5))
	order_number = timestamp + random_number
	attraction_id = orderInfo.order.trip.attraction.id
	order_date = orderInfo.order.trip.date
	order_time = orderInfo.order.trip.time
	order_price = orderInfo.order.price
	contact_name = orderInfo.order.contact.name
	contact_email = orderInfo.order.contact.email
	contact_phone = orderInfo.order.contact.phone
	# 檢查景點是否存在
	query = "SELECT id FROM spot WHERE id = %s"
	data = execute_query(query, (attraction_id,), dictionary = True)
	if not data:
		return JSONResponse(content = {"error": True, "message": "Attraction not found"}, status_code = 400)
	# 檢查時間與價格是否搭配
	if (order_time == "morning" and order_price != 2000) or (order_time == "afternoon" and order_price != 2500):
		return JSONResponse(content = {"error": True, "message": "Price must be 2000 for morning and 2500 for afternoon"}, status_code = 400)
	query = "INSERT INTO orders (order_number, user_id, spot_id, date, time, price, contact_name, contact_email, contact_phone) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
	execute_query(query, (order_number, user_id, attraction_id, order_date, order_time, order_price, contact_name, contact_email, contact_phone))
	
	URL = "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime"
    
	payment_info = {
        "prime": orderInfo.prime,
        "partner_key": partner_key,
		"amount": order_price,
        "merchant_id": "jamyyu_CTBC",
        "details": "TapPay Test",
        "cardholder": {
            "phone_number": contact_phone,
            "name": contact_name,
            "email": contact_email
        },
        "remember": False
    }

    # 將支付信息轉換為 JSON 字符串
	data = json.dumps(payment_info).encode("utf-8")

	headers = {
        "Content-Type": "application/json",
        "x-api-key": partner_key
    }

    # 創建請求對象
	request = req.Request(URL, data = data, headers = headers)
	with req.urlopen(request) as response:
		response_data = response.read().decode("utf-8")
		response_json = json.loads(response_data) # 把原始JSON資料解析成字典/列表格式
		if response_json["status"] == 0:
			#print("Payment successful!")
			#print("Response:", response_json)
			query = "UPDATE orders SET status = 'PAID' WHERE order_number = %s"
			execute_query(query, (order_number,))
			query = "DELETE FROM booking WHERE user_id = %s"
			execute_query(query, (user_id,))
			return Data( data = {"number": order_number,"payment": {"status": 0,"message": "付款成功"}})
		else:
			#print("Payment failed!")
			#print("Response:", response_json)
			query = "DELETE FROM booking WHERE user_id = %s"
			execute_query(query, (user_id,))
			return Data( data = {"number": order_number,"payment": {"status": response_json["status"], "message": response_json["msg"]}})
		
	
