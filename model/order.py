import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import random
import re
from fastapi import *
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os 
from dbconfig import Database
from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal, Union
import json
import jwt
from datetime import date, datetime
import urllib.request as req


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
class Error(BaseModel):
	error: bool
	message: str
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


load_dotenv()
key = os.getenv("mykey")
partner_key = os.getenv("partner_key")


class OrderModel:
    async def order(orderInfo, token):
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
        data = Database.execute_query(query, (attraction_id,), dictionary = True)
        if not data:
            return JSONResponse(content = {"error": True, "message": "Attraction not found"}, status_code = 400)
        # 檢查時間與價格是否搭配
        if (order_time == "morning" and order_price != 2000) or (order_time == "afternoon" and order_price != 2500):
            return JSONResponse(content = {"error": True, "message": "Price must be 2000 for morning and 2500 for afternoon"}, status_code = 400)
        query = "INSERT INTO orders (order_number, user_id, spot_id, date, time, price, contact_name, contact_email, contact_phone) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        Database.execute_query(query, (order_number, user_id, attraction_id, order_date, order_time, order_price, contact_name, contact_email, contact_phone))
        
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
            response_json = json.loads(response_data)
            if response_json["status"] == 0:
                query = "UPDATE orders SET status = 'PAID' WHERE order_number = %s"
                Database.execute_query(query, (order_number,))
                query = "DELETE FROM booking WHERE user_id = %s"
                Database.execute_query(query, (user_id,))
                return Data( data = {"number": order_number,"payment": {"status": 0,"message": "付款成功"}})
            else:
                query = "DELETE FROM booking WHERE user_id = %s"
                Database.execute_query(query, (user_id,))
                return Data( data = {"number": order_number,"payment": {"status": response_json["status"], "message": response_json["msg"]}})
						
    async def get_order(order_number: str, token):
		# 驗證 JWT 並獲取 user_id
        try:
            payload = jwt.decode(token, key, algorithms = "HS256")
            user_id = payload["id"]
        except:
            return JSONResponse(content = {"error": True, "message": "Not logged in, access denied"}, status_code = 403) 
        # 查詢資料庫中的訂單資訊並聯結景點資料
        query = """
        SELECT o.order_number, o.user_id, o.spot_id, o.date, o.time, o.price, 
               o.contact_name, o.contact_email, o.contact_phone, o.status, 
               s.name AS spot_name, s.address AS spot_address, s.images AS spot_images
        FROM orders o
        JOIN spot s ON o.spot_id = s.id
        WHERE o.order_number = %s AND o.user_id = %s
        """
        order = Database.execute_query(query, (order_number, user_id), dictionary=True)

        if not order:
            return JSONResponse(content={"data": None}, status_code=200)

        order_data = order[0]
        order_data["spot_images"] = json.loads(order_data["spot_images"])
        # 構建返回的訂單資料
        result = {
            "order_number": order_data["order_number"],
            "user_id": order_data["user_id"],
            "spot": {
                "id": order_data["spot_id"],
                "name": order_data["spot_name"],
                "address": order_data["spot_address"],
                "image": order_data["spot_images"][0]
            },
            "date": order_data["date"].isoformat(),
            "time": order_data["time"],
            "price": order_data["price"],
            "contact": {
                "name": order_data["contact_name"],
                "email": order_data["contact_email"],
                "phone": order_data["contact_phone"]
            },
            "status": order_data["status"],
        }
        return JSONResponse(content={"data": result}, status_code=200)         