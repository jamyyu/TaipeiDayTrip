from typing import Union
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
class Data(BaseModel):
	data: Union [list, dict, str, Attraction]
class Error(BaseModel):
	error: bool
	message: str


class MRTModel:
    async def mrt_list():
        query = "SELECT name FROM mrt GROUP BY name ORDER BY COUNT(name) DESC"
        data = Database.execute_query(query)
        new_data = []
        for mrt in data:
            if mrt[0] != None:
                new_data.append(mrt[0])
        return Data(data = new_data)