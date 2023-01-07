from fastapi import FastAPI
from mangum import Mangum

try:
    from dotenv import load_dotenv

    load_dotenv()
except:
    pass

from .api import links, users

app = FastAPI()
handler = Mangum(app)

app.include_router(links.router)
app.include_router(users.router)


@app.get('/')
async def home():
    return {"Message": "Link manager API, use with caution."}
