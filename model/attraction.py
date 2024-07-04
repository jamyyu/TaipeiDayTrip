import json
from typing import Union
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dbconfig import Database


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
class SearchAttractionsData(BaseModel):
	nextPage: Union [int, None] = None
	data: Union [Attraction, list, None] = []
class Data(BaseModel):
	data: Union [list, dict, str, Attraction]
class Error(BaseModel):
	error: bool
	message: str
    

class AttractionModel:
    async def search_attractions_data(page:int, keyword:str):
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
            data = Database.execute_query(query, params = (limit+1, offset), dictionary = True)
        else:
            query = "SELECT name FROM mrt GROUP BY name ORDER BY COUNT(name) DESC"
            data = Database.execute_query(query, params = None, dictionary = True)
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
                data = Database.execute_query(query, params = (keyword, limit+1, offset), dictionary = True)
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
                data = Database.execute_query(query, params = (f"%{keyword}%", limit+1, offset), dictionary = True)
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
    
    async def read_attractionId(attractionId: int):
        query = """SELECT spot.id, spot.name, category.name AS category, spot.description, spot.address, spot.transport, mrt.name AS mrt, spot.lat, spot.lng, spot.images 
        FROM spot INNER JOIN mrt ON spot.id = mrt.spot_id 
        INNER JOIN category ON spot.id = category.spot_id 
        WHERE spot.id = %s"""
        data = Database.execute_query(query, (attractionId,), dictionary = True)
        if not data:
            return JSONResponse(content = {"error": True, "message": "Attraction not found"}, status_code = 400)
        if "images" in data[0]:
            data[0]["images"] = json.loads(data[0]["images"])
            return Data(data = Attraction(**data[0]))