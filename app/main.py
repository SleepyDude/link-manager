from fastapi import FastAPI
from mangum import Mangum

from .api import links

app = FastAPI()
handler = Mangum(app)

app.include_router(links.router)


@app.get('/')
async def home():
    return {"Message": "Link manager API, use with caution."}
