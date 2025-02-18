from fastapi import FastAPI, WebSocket, status, HTTPException, WebSocketDisconnect, WebSocketException
from fastapi.responses import JSONResponse
from typing import List, Dict, Set
import json

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

class MessageHandler:
    @staticmethod
    async def handle_text(websocket: WebSocket, message: str):
        try:
            processed_message = message.upper()
            await websocket.send_text(processed_message)
        except Exception as e:
            raise WebSocketException(code=1003, reason=str(e))

    @staticmethod
    async def handle_json(websocket: WebSocket, message: Dict):
        try:
            response = {
                "type": "json",
                "data": message
            }
            await websocket.send_json(response)
        except Exception as e:
            raise WebSocketException(code=1003, reason=str(e))

    @staticmethod
    async def handle_binary(websocket: WebSocket, data: bytes):
        try:
            await websocket.send_bytes(data)
        except Exception as e:
            raise WebSocketException(code=1003, reason=str(e))

manager = ConnectionManager()
handler = MessageHandler()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await manager.connect(websocket)
        while True:
            try:
                data = await websocket.receive()
                
                if "text" in data:
                    await MessageHandler.handle_text(websocket, data["text"])
                elif "json" in data:
                    await MessageHandler.handle_json(websocket, data["json"])
                elif "bytes" in data:
                    await MessageHandler.handle_binary(websocket, data["bytes"])
                else:
                    raise WebSocketException(code=1003, reason="Unsupported message format")
                    
            except WebSocketDisconnect:
                manager.disconnect(websocket)
                await manager.broadcast(f"Client disconnected")
                break
                
            except Exception as e:
                manager.disconnect(websocket)
                await websocket.close(code=1003, reason=str(e))
                break
                
    except Exception as e:
        if websocket in manager.active_connections:
            manager.disconnect(websocket)
        raise WebSocketException(code=1003, reason=str(e))