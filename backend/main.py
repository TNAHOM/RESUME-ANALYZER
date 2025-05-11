from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

from backend.auth import router as auth_router
from backend.upload import router as upload_router

app.include_router(auth_router, prefix="/auth")
app.include_router(upload_router)

storage_path = os.path.join(os.path.dirname(__file__), "../storage")
app.mount("/storage", StaticFiles(directory=storage_path), name="storage")
