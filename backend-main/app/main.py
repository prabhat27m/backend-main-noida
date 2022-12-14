from .admin_routes import get_current_admin
from fastapi import FastAPI
from .analytics import stats_router
from .auth_routes import auth_router
from .admin_routes import admin_router
from .student_routes import itemrouter
from fastapi_jwt_auth import AuthJWT
from .schemas import Settings
import os
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status

load_dotenv()

origins = ["*"]

security = HTTPBasic()

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware


app=FastAPI()


@AuthJWT.load_config
def get_config():
    return Settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(admin_router)

app.include_router(itemrouter,include_in_schema=True)
app.include_router(stats_router,include_in_schema=True)
