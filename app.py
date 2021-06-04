from fastapi import FastAPI

app = FastAPI()

@app.get("/user/{user_id}")
def get_user(user_id: int):
	return user_id

@app.get("/")
async def root():
    return {"message": "Hello World"}