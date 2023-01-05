from fastapi import FastAPI, Body, HTTPException
from mangum import Mangum
from app.models.link_mod import PutLinkRequest
from uuid import uuid4
import os

try:
    import boto3
    from boto3.dynamodb.conditions import Key
except:
    pass

app = FastAPI()
handler = Mangum(app)


@app.get('/')
async def home():
    return {"Message": "Botay or die, hello API!"}

@app.put('/add_link')
async def add_link(put_link_request: PutLinkRequest):
    item = {
        'PK': f'USER#{put_link_request.user_id}',
        'SK': f'ULINK#{uuid4().hex}',
        'user_id': put_link_request.user_id,
        'title': put_link_request.title,
        'url': put_link_request.url,
        'link_id': f'{uuid4().hex}'
    }

    table = _get_table()
    table.put_item(Item=item)
    return {'link': item}

@app.get('/get_link/{link_id}')
async def get_link(link_id: str):
    table = _get_table()
    response = table.get_item(Key={"link_id": link_id})
    item = response.get("Item")
    if item is None:
        raise HTTPException(404, detail=f'Link {link_id} not found')
    return item

@app.get('/list_links/{user_id}')
async def get_links(user_id: str):
    table = _get_table()
    response = table.query(
        IndexName='user-index',
        KeyConditionExpression=Key('user_id').eq(user_id),
        ScanIndexForward=False,
        Limit=10,
    )
    links = response.get('Items')
    return {'links': links}

@app.put('/update_link')
async def update_link(put_link_request: PutLinkRequest):
    table = _get_table()
    table.update_item(
        Key={'link_id': put_link_request.link_id},
        UpdateExpression='SET title = :title, url = :url',
        ExpressionAttributeValues={
            ':title': put_link_request.title,
            ':url': put_link_request.url
        },
        ReturnValues='ALL_NEW'
    )
    

def _get_table():
    table_name = os.environ.get('TABLE_NAME')
    return boto3.resource('dynamodb').Table(table_name)