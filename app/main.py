from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from mangum import Mangum
from fastapi.openapi.utils import get_openapi

try:
    from dotenv import load_dotenv

    load_dotenv()
except:
    pass

from .api import links, users, auth

tags_metadata = [
    {
        "name": "Auth",
        "description": "Methods for getting and refresh tokens",
    },
    {
        "name": "Users",
        "description": "Operations with users.",
    },
    {
        "name": "Links",
        "description": "Manage links."
    },
    {
        "name": "ags",
        "description": "Link tagging."
    },
]

app = FastAPI(openapi_tags=tags_metadata)
handler = Mangum(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(links.router)



@app.get('/')
async def home():
    return RedirectResponse(url='/docs')

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Link Manager API",
        version="0.0.1",
        description="This is a custom OpenAPI schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi