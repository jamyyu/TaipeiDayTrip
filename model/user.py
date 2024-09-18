from typing import Union
from fastapi import *
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from dbconfig import Database
import bcrypt
from datetime import datetime, timedelta
import jwt
from dotenv import load_dotenv
import os
from fastapi.security import OAuth2PasswordBearer 

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
class UserSignup(BaseModel):
	name: str
	email: EmailStr
	password: str
class UserSignin(BaseModel):
	email: str
	password: str
class Success(BaseModel):
	ok: bool
class Error(BaseModel):
	error: bool
	message: str
class Token(BaseModel):
	token: str
class Data(BaseModel):
	data: Union [list, dict, str, Attraction]
     

load_dotenv()
key = os.getenv("mykey")


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/api/user/auth")

class UserModel:
    async def signup(user: UserSignup):
        query = "SELECT email FROM user WHERE email=%s"
        name = user.name
        email = user.email
        password =user.password
        data = Database.execute_query(query, (email,), dictionary = True)
        if data:
            return JSONResponse(content = {"error": True, "message": "Email already registered"}, status_code = 400)
        else:
            hashed_password = hash_password(password)
            query = "INSERT INTO user (name, email, password) VALUES (%s, %s, %s)"
            Database.execute_query(query, (name, email, hashed_password))
            return Success(ok = True)
    
    async def signin(user: UserSignin):
        email = user.email
        password = user.password
        query = "SELECT id, name, email, password FROM user WHERE email = %s"
        data = Database.execute_query(query, (email,), dictionary = True)
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
            "exp": exp_timestamp 
            }
            encoded = jwt.encode(payload, key, algorithm = "HS256")
            return Token(token = encoded)
    
    async def check_auth(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(token, key, algorithms = "HS256")
            return Data(data = {"id": payload["id"], "name": payload["name"], "email": payload["email"]})
        except:
            return Data(data = "null")
        