#!/usr/bin/env python3
"""SelfPrivacy server management API"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

import uvicorn

from selfprivacy_api.dependencies import get_api_version
from selfprivacy_api.graphql.schema import schema
from selfprivacy_api.migrations import run_migrations

from selfprivacy_api.rest import (
    users,
    api_auth,
    services,
)

app = FastAPI()

graphql_app = GraphQLRouter(
    schema,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(users.router)
app.include_router(api_auth.router)
app.include_router(services.router)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/api/version")
async def get_version():
    """Get the version of the server"""
    return {"version": get_api_version()}


@app.on_event("startup")
async def startup():
    run_migrations()


if __name__ == "__main__":
    uvicorn.run(
        "selfprivacy_api.app:app", host="127.0.0.1", port=5050, log_level="info"
    )
