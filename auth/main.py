from fastapi import FastAPI,HTTPException,Depends,status
from fastapi.responses import JSONResponse
from schema.auth import LoginSchema,DeleteSchema,RegisterSchema,UpdateSchema
app=FastAPI()



fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

#query


@app.get("/simple_query",status_code=status.HTTP_200_OK)
async def page(skip:int=0,limit:int=10):
    try:
        return fake_items_db[skip:skip+limit]
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    
@app.get("/test",status_code=status.HTTP_200_OK)
async def test_query(name:str):
    try:
        for i in fake_items_db:
            if i.keys==name:
                return JSONResponse(
                    {"result":f"{i.values}"},
                    status_code=status.HTTP_202_ACCEPTED,
                )
        pass
        return JSONResponse(
            {"result":"not found"},
            status_code=status.HTTP_204_NO_CONTENT
        )
    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
        )


@app.post("/login", status_code=200)
async def login(payload: LoginSchema):
    try:
        print("Login attempt with:", payload)
        return  JSONResponse(
            {"message": "Login successful",
             "user _data": {
                 "username": payload.password,
                 "email": payload.email
             }},
            status_code=200
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

@app.post("/register", status_code=201)
async def register(payload: RegisterSchema):
    try:
        print("Registration attempt with:", payload)
        user_data=payload.model_dump()
        return JSONResponse(
            {"message": "Registration successful",
             "user _data": {
                 "username": user_data['username'],
                 "email": user_data['email'],
                 "password": user_data['password'],
                 "confirm_password": user_data['confirm_password'],
             }},
            status_code=201
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="Registration failed"
        )

@app.delete("/delete", status_code=200)
async def delete(payload: DeleteSchema):
    try:
        print("Logout attempt for user:", payload.user_id)
        return JSONResponse(
            {"message": "Logout successful"},
            status_code=200
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="Logout failed"
        )

@app.put("/update", status_code=200)
async def update(payload: UpdateSchema):
    try:
        print("Update attempt with:", payload)
        return JSONResponse(
            {"message": "Update successful"},
            status_code=200,
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="Update failed"
        )