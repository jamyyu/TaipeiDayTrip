from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
import os
import mysql.connector
from mysql.connector import pooling
app=FastAPI()


load_dotenv()
mypassword = os.getenv("mypassword")

pool = pooling.MySQLConnectionPool(
	pool_name="mypool",
    pool_size=5,  
    pool_reset_session=True,
    host="localhost",
    database="TaipeiDayTrip",
    user="root",
    password=mypassword
)

def execute_query(query, params=None, dictionary=False):
    try:
        cnx = pool.get_connection()
        if cnx.is_connected():
            cursor = cnx.cursor(dictionary=dictionary)
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


@app.get("/api/attrtions")
async def index(request: Request):
	pass


@app.get("/api/attraction/{attractionId}")
async def read_attractionId(request: Request, attractionId: int):
	query = """SELECT spot.id, spot.name, category.name AS category, spot.description, spot.address, spot.transport, mrt.name AS mrt, spot.lat, spot.lng, spot.images 
    FROM spot INNER JOIN mrt ON spot.id = mrt.spot_id 
    INNER JOIN category ON spot.id = category.spot_id 
    WHERE spot.id = %s"""
	data = execute_query(query, (attractionId,), dictionary=True)
	if not data:
		raise HTTPException(status_code=404, detail="Attraction not found")
	return JSONResponse(content={"data":data[0]})

@app.get("/api/mrts")
async def serch_mrt():
	query = "SELECT name FROM mrt GROUP BY name ORDER BY COUNT(name) DESC"
	data = execute_query(query)
	newData = []
	for mrt in data:
		if mrt[0]!= None:
			newData.append(mrt[0])
	return JSONResponse(content={"data":newData})

