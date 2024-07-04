from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
import os 
from fastapi.staticfiles import StaticFiles
from router.attraction import AttractionRouter
from router.mrt import MRTRouter
from router.user import UserRouter
from router.booking import BookingRouter
from router.order import OrderRouter

app = FastAPI()

app.mount("/static", StaticFiles(directory = "static"), name = "static")

load_dotenv()
mypassword = os.getenv("mypassword")
key = os.getenv("mykey")
partner_key = os.getenv("partner_key")


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

app.include_router(AttractionRouter)
app.include_router(MRTRouter)
app.include_router(UserRouter)
app.include_router(BookingRouter)
app.include_router(OrderRouter)

