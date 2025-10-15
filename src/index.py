from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class SumBody(BaseModel):
    a: float
    b: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/sum")
def sum_numbers(body: SumBody):
    try:
        return {"result": body.a + body.b}
    except Exception:
        raise HTTPException(status_code=400, detail="a and b must be numbers")