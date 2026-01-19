import asyncio
import websockets

async def test():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        print("Connected to WS")
        while True:
            msg = await websocket.recv()
            print(f"Received: {msg}")

asyncio.run(test())
