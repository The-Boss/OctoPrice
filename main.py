#initial code

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello":"George"}

@app.get("/price")
async def read_root():
    return {"colour":"red"}

