import json
import re
import os
from dotenv import load_dotenv
import mysql.connector


with open("taipei-attractions.json", "r", encoding="utf-8") as file:
    data = json.load(file)
spot_list = data["result"]["results"]


filtered_spot_list=[]
for spot in spot_list:
    #img篩選
    imgurls=re.findall(r"https?://.*?\.(?:jpg|JPG|png|PNG)", spot["file"], re.IGNORECASE)
    #台北市後面空格移除
    address = spot["address"]
    address_no_space = address.replace(" ", "")
    filtered_spot_list.append({"id":spot["_id"] ,"name":spot["name"], "category":spot["CAT"], "description":spot["description"], "address":address_no_space, 
                      "transport":spot["direction"], "mrt":spot["MRT"], "lat":spot["latitude"], "lng":spot["longitude"], "images":imgurls})

load_dotenv()
mypassword = os.getenv("mypassword")

con=mysql.connector.connect(
    user="root",
    password=mypassword,
    host="localhost",
    database="TaipeiDayTrip"
)
cursor=con.cursor()


for spot in filtered_spot_list:
   images_json = json.dumps(spot["images"])
   cursor.execute("INSERT INTO spot (id, name, description, address, transport, lat, lng, images) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                  (spot["id"], spot["name"], spot["description"], spot["address"], spot["transport"], spot["lat"], spot["lng"], images_json))
   con.commit()
   cursor.execute("INSERT INTO mrt (spot_id, name) VALUES (%s, %s)",
                  (spot["id"], spot["mrt"]))
   con.commit()
   cursor.execute("INSERT INTO category (spot_id, name) VALUES (%s, %s)",
                  (spot["id"], spot["category"]))
   con.commit()