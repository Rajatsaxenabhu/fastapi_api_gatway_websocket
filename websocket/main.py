from fastapi import FastAPI, WebSocket, status, HTTPException, WebSocketDisconnect, WebSocketException
from fastapi.responses import JSONResponse
from typing import List, Dict
import json

app = FastAPI()

clients: List[WebSocket] = []

async def handle_text(websocket: WebSocket, message: str):
    try:
        processed_message = message.upper()
        response = {
            "type": "text",
            "processed": processed_message
        }
        await websocket.send_json(response)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })

async def handle_json(websocket: WebSocket, message: Dict):
    try:
        response = {
            "type": "json",
            "data": message
        }
        await websocket.send_json(response)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })

async def handle_binary(websocket: WebSocket, data: bytes):
    try:
        await websocket.send_json({
            "type": "binary",
            "size": len(data)
        })
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })

@app.websocket("/")
async def websocket_test(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    
    try:
        while True:
            try:
                data = await websocket.receive()
                
                if "text" in data:
                    try:
                        message = json.loads(data["text"])
                        await handle_json(websocket, message)
                    except json.JSONDecodeError:
                        await handle_text(websocket, data["text"])
                        
                elif "bytes" in data:
                    await handle_binary(websocket, data["bytes"])
                    
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "error": str(e)
                })
                
    except WebSocketDisconnect:
        clients.remove(websocket)
    except Exception as e:
        if websocket in clients:
            clients.remove(websocket)