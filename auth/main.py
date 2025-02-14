from fastapi import FastAPI,HTTPException,Depends
from fastapi.responses import JSONResponse
from schema.auth import LoginSchema,DeleteSchema,RegisterSchema,UpdateSchema
app=FastAPI()


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