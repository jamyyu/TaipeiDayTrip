import json
from typing import Literal, Union
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from dbconfig import Database
from datetime import date
import jwt
from dotenv import load_dotenv
import os


class Success(BaseModel):
	ok: bool
class Error(BaseModel):
	error: bool
	message: str
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
     

load_dotenv()
key = os.getenv("mykey")


class BookingModel:
    async def booking(bookingInfo, token):
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
        data = Database.execute_query(query, (attraction_id,), dictionary = True)
        if not data:
            return JSONResponse(content = {"error": True, "message": "Attraction not found"}, status_code = 400)
        # 檢查時間與價格是否搭配
        if (booking_time == "morning" and booking_price != 2000) or (booking_time == "afternoon" and booking_price != 2500):
            return JSONResponse(content = {"error": True, "message": "Price must be 2000 for morning and 2500 for afternoon"}, status_code = 400)
        # 預定資料寫入資料庫
        query = "SELECT id FROM booking WHERE user_id = %s"
        bookingData = Database.execute_query(query, (user_id,))
        if not bookingData:
            query = "INSERT INTO booking (user_id, spot_id, date, time, price) VALUES (%s, %s, %s, %s, %s)"
            Database.execute_query(query, (user_id, attraction_id, booking_date, booking_time, booking_price))
        else:
            query = "UPDATE booking SET spot_id = %s, date = %s, time = %s, price = %s WHERE user_id = %s"
            Database.execute_query(query, (attraction_id, booking_date, booking_time, booking_price, user_id))
        return Success(ok = True)
    
    async def get_booking(token):
        try:
            payload = jwt.decode(token, key, algorithms = "HS256")
            user_id = payload["id"]
        except:
            return JSONResponse(content = {"error": True, "message": "Not logged in, access denied"}, status_code = 403)
        query = "SELECT * FROM booking WHERE user_id = %s"
        booking_data = Database.execute_query(query, (user_id,), dictionary=True)
        if booking_data:
            booking_data = booking_data[0]
            spot_id = booking_data["spot_id"]
            query = "SELECT name, address, images FROM spot WHERE id = %s"
            attraction_data = Database.execute_query(query, (spot_id,), dictionary=True)
            attraction_data = attraction_data[0]
            if "images" in attraction_data:
                attraction_data["images"] = json.loads(attraction_data["images"])
            return Data(data = {"attraction":{"id": spot_id, "name": attraction_data["name"], "address": attraction_data["address"], "image":attraction_data["images"][0]}, 
                            "date": booking_data["date"].isoformat(), "time": booking_data["time"], "price": booking_data["price"]})
        else:
            return Data(data = "null")
        
    async def delete_booking(token):
        try:
            payload = jwt.decode(token, key, algorithms = "HS256")
            user_id = payload["id"]
        except:
            return JSONResponse(content = {"error": True, "message": "Not logged in, access denied"}, status_code = 403)
        query = "SELECT * FROM booking WHERE user_id = %s"
        booking_data = Database.execute_query(query, (user_id,), dictionary=True)
        if booking_data:
            query = "DELETE FROM booking WHERE user_id = %s"
            Database.execute_query(query, (user_id,))
        return Success(ok = True)