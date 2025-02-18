from fastapi import FastAPI, WebSocket, WebSocketDisconnect, WebSocketException
from typing import Set
import json


# Sending data
# await websocket.send_text(data)
# await websocket.send_bytes(data)
# await websocket.send_json(data)
# JSON messages default to being sent over text data frames, from version 0.10.0 onwards. Use websocket.send_json(data, mode="binary") to send JSON over binary data frames.

# Receiving data
# await websocket.receive_text()
# await websocket.receive_bytes()
# await websocket.receive_json()
# May raise starlette.websockets.WebSocketDisconnect().

# JSON messages default to being received over text data frames, from version 0.10.0 onwards. Use websocket.receive_json(data, mode="binary") to receive JSON over binary data frames.




app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        

class MessageHandler:
    @staticmethod
    async def handle_message(websocket: WebSocket, message_type: str, data: any):
        try:
            if message_type == "text":
                processed_message = data.upper()
                await websocket.send_text(processed_message)
                
            elif message_type == "json":
                json_data = data if isinstance(data, dict) else json.loads(data)
                response = {
                    "type": "json",
                    "data": json_data
                }
                await websocket.send_json(response)
                
            elif message_type == "binary":
                await websocket.send_bytes(data)
                
            else:
                raise WebSocketException(code=1003, reason=f"Unsupported message type: {message_type}")
                
        except json.JSONDecodeError:
            raise WebSocketException(code=1003, reason="Invalid JSON format")
        except Exception as e:
            raise WebSocketException(code=1003, reason=str(e))

manager = ConnectionManager()

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await manager.connect(websocket)
        await websocket.send_text("Connected to WebSocket server")
        
        while True:
            try:
                message = await websocket.receive_text() #raw data liya 
                await websocket.send(message.upper())
                # message_type = message.get("type")
                
                # if message_type == "websocket.disconnect":
                #     raise WebSocketDisconnect(code=1000, reason="Client disconnected")
                
                # if message_type == "websocket.receive":
                #     data = message.get("text") or message.get("bytes") or message.get("data")
                    
                #     if isinstance(data, str):
                #         try:
                #             json_data = json.loads(data)
                #             await MessageHandler.handle_message(websocket, "json", json_data)
                #         except json.JSONDecodeError:
                #             await MessageHandler.handle_message(websocket, "text", data)
                #     elif isinstance(data, bytes):
                #         await MessageHandler.handle_message(websocket, "binary", data)
                
            except WebSocketDisconnect:
                manager.disconnect(websocket)
                break
                
            except Exception as e:
                await websocket.send_text(f"Error: {str(e)}")
                continue
                
    except Exception as e:
        raise WebSocketException(code=1003, reason=str(e))
