from fastapi import FastAPI,WebSocket,status,HTTPException,WebSocketDisconnect,WebSocketException
from fastapi.responses import JSONResponse
from typing import List

app=FastAPI()

clients:List[WebSocket]=[]

@app.websocket("/ws")
async def websocket_test(websocket:WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data=await websocket.receive_text()
            await websocket.send_text({data.upper()})
    except WebSocketDisconnect:
        clients.remove(websocket)

@app.post('/testing')
def tesing():
    try:
        print("thesting the websocket")
        return JSONResponse({
            "message":"testing the websocket",
        },status_code=status.HTTP_202_ACCEPTED
        )
    except HTTPException as e:
        print("htp exception is ",str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print("exception is ",str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
