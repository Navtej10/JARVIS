import asyncio
import websockets
import json

async def test_client():
    uri = "ws://localhost:8765"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected.")
            
            # Send fake register_object
            payload = {
                "type": "register_object",
                "id": "test_panel_1",
                "kind": "panel",
                "bounds": {"x": 100, "y": 100, "width": 400, "height": 300},
                "z_index": 10
            }
            await websocket.send(json.dumps(payload))
            print("Sent register_object payload.")
            
            print("Listening for incoming gesture events... (Perform gestures in front of the camera!)")
            async for message in websocket:
                print(f"Received from server: {message}")
                
    except ConnectionRefusedError:
        print("Connection refused. Is the bridge server running?")

if __name__ == "__main__":
    asyncio.run(test_client())
