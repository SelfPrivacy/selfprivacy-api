import pytest
from fastapi import FastAPI, WebSocket
import uvicorn

# import subprocess
from multiprocessing import Process
import asyncio
from time import sleep
from websockets import client

app = FastAPI()


@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"You sent: {data}")


def run_uvicorn():
    uvicorn.run(app, port=5000)
    return True


@pytest.mark.asyncio
async def test_uvcorn_ws_works_in_prod():
    proc = Process(target=run_uvicorn)
    proc.start()
    sleep(2)

    ws = await client.connect("ws://127.0.0.1:5000")

    await ws.send("hohoho")
    message = await ws.read_message()
    assert message == "You sent: hohoho"
    await ws.close()
    proc.kill()
