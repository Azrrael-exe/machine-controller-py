import uvicorn
from fastapi import FastAPI
from redis import Redis

from domain.values import Read, get_read_from_redis

app = FastAPI()

redis_client = Redis(host="redis", port=6379, db=0)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/reads/{source}")
def read_read(source: int):
    return get_read_from_redis(redis_client, source)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
