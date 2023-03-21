from fastapi import FastAPI, Request
from routes.expediente import expediente
from routes.usuarios import user

from starlette.middleware.cors import CORSMiddleware

from data.data import server

app = FastAPI()

@app.middleware("http")
async def print_request_headers(request: Request, call_next):
    print(request.headers)
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

'''app.add_middleware(
    CORSMiddleware,
    allow_origins=[server],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''

app.include_router(expediente)
app.include_router(user)