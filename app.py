import json
from enum import Enum
from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from domain.values import Read, Units, load_reads, save_reads

app = FastAPI()


class ReadModel(BaseModel):
    value: int
    source: int
    units: Units


reads = load_reads()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/reads", response_model=List[ReadModel])
def get_all_reads():
    return [ReadModel(**read.__dict__) for read in reads.values()]


@app.get("/reads/{source}", response_model=ReadModel)
def read_read(source: int):
    if source not in reads:
        raise HTTPException(status_code=404, detail="Read not found")
    return ReadModel(**reads[source].__dict__)


@app.post("/reads", response_model=ReadModel)
def create_read(read: ReadModel):
    if read.source in reads:
        raise HTTPException(
            status_code=400, detail="Read with this source already exists"
        )
    reads[read.source] = Read(**read.dict())
    save_reads(reads)
    return read


@app.put("/reads/{source}", response_model=ReadModel)
def update_read(source: int, read: ReadModel):
    if source != read.source:
        raise HTTPException(
            status_code=400, detail="Source in path must match source in body"
        )
    if source not in reads:
        raise HTTPException(status_code=404, detail="Read not found")
    reads[source] = Read(**read.dict())
    save_reads(reads)
    return read


@app.delete("/reads/{source}")
def delete_read(source: int):
    if source not in reads:
        raise HTTPException(status_code=404, detail="Read not found")
    del reads[source]
    save_reads(reads)
    return {"message": "Read deleted successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
