from fastapi import FastAPI,HTTPException,Depends,status
from fastapi.responses import JSONResponse
from schema.auth import LoginSchema,DeleteSchema,Multi_query,UpdateSchema
app=FastAPI()



fake_items_db = [{"aman": "doc_1"}, {"singh": "doc_2"}, {"raj": "doc_3"}]



# get all 
@app.get("/",status_code=status.HTTP_200_OK)
async def get(skip:int=0,limit:int=10):
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content= fake_items_db[skip:skip+limit]
        )
    
    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
    )
    
# get by name or query string
@app.get("/test",status_code=status.HTTP_200_OK)
async def get_query(name:str):
    try:
        print("name",name)
        for item in fake_items_db:
            for key,value in item.items():
                if key==name:
                    return JSONResponse(
                        content=f"{key} value is {value}",
                        status_code=status.HTTP_200_OK,
                    )
        return JSONResponse(
            content="not found",
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
    )

# multi qeury paramenetr

@app.get("/test_bool")
async def multi_query(name:str,values:str):
    try:
        for item in fake_items_db:
            for key,value in item.items():
                if key==name and value==values:
                    return JSONResponse(
                        content="Found in db",
                        status_code=status.HTTP_200_OK
                    )
        return JSONResponse(
            content="Not found in DB",
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
    )


# post

@app.post("/login", status_code=status.HTTP_200_OK)
async def login(payload: LoginSchema):
    try:
        print("Login attempt with:", payload)
        return JSONResponse(
            content={ 
                "message": "Login successful",
                "user_data": { 
                    "username": payload.password,
                    "email": payload.email
                }
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )  
    

#delete
@app.delete("/delete", status_code=status.HTTP_200_OK)
async def delete(payload: DeleteSchema):
    try:
        print("Logout attempt for user:", payload.user_id)
        return JSONResponse(
            {"message": "Logout successful"},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

#update

@app.put("/update", status_code=200)
async def update(payload: UpdateSchema):
    try:
        print("Update attempt with:", payload)
        return JSONResponse(
            {"message": "Update successful"},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update failed"
        )