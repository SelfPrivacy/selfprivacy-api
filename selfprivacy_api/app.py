#!/usr/bin/env python3
"""SelfPrivacy server management API"""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from contextlib import asynccontextmanager

import uvicorn

from selfprivacy_api.dependencies import get_api_version
from selfprivacy_api.graphql.schema import schema
from selfprivacy_api.migrations import run_migrations

from starlette.middleware.sessions import SessionMiddleware
from secrets import token_urlsafe

from selfprivacy_api.userpanel.routes.login import router as login_router
from selfprivacy_api.userpanel.routes.user import router as user_router
from selfprivacy_api.userpanel.routes.internal import router as internal_router

from selfprivacy_api.userpanel.static import static_dir


log_level = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO), format="%(levelname)s: %(message)s"
)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    run_migrations()
    yield


app = FastAPI(lifespan=app_lifespan)

graphql_app: GraphQLRouter = GraphQLRouter(
    schema,
    subscription_protocols=[
        GRAPHQL_TRANSPORT_WS_PROTOCOL,
        GRAPHQL_WS_PROTOCOL,
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

secret_key = token_urlsafe(32)
app.add_middleware(SessionMiddleware, secret_key=secret_key)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(graphql_app, prefix="/graphql")
app.include_router(login_router, prefix="/login")
app.include_router(user_router, prefix="/user")
app.include_router(internal_router, prefix="/internal")


@app.get("/api/version")
async def get_version():
    """Get the version of the server"""
    return {"version": get_api_version()}


@app.get("/")
async def root():
    return RedirectResponse(url="/user")


if __name__ == "__main__":
    uvicorn.run(
        "selfprivacy_api.app:app", host="127.0.0.1", port=5050, log_level="info"
    )
