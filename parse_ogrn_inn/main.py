from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from parse_ogrn_nalog import scrape_ogrn_info

app = FastAPI()


class OGRNRequest(BaseModel):
    ogrn_or_inn: str


@app.post("/get-info")
def get_info(request: OGRNRequest):
    try:
        data = scrape_ogrn_info(request.ogrn_or_inn)
        if data:
            return data
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)