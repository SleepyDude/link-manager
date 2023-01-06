from fastapi import APIRouter, HTTPException
from uuid import uuid4
from datetime import datetime
try:
    from boto3.dynamodb.conditions import Key
except:
    pass



from ..db import _get_table
from ..models.link_mod import PutLinkRequest

router = APIRouter()

# TODO made dependaple of access token (login)
@router.put('/add_link')
async def add_link(put_link_request: PutLinkRequest):
    link_id = uuid4().hex # generate link id
    # now it's public
    user_id = 'test_user'
    item = {
        'PK': f'USER#{user_id}',
        'SK': f'ULINK#{link_id}',
        'Type': 'Link',
        'created': str(datetime.utcnow()),
        'title': put_link_request.title,
        'url': put_link_request.url,
    }
    table = _get_table()
    table.put_item(Item=item)
    return {'link': item}

'''
@router.get('/get_link/{link_id}')
async def get_link(link_id: str):
    table = _get_table()
    response = table.get_item(Key={"link_id": link_id})
    item = response.get("Item")
    if item is None:
        raise HTTPException(404, detail=f'Link {link_id} not found')
    return item

@router.get('/list_links/{user_id}')
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

@router.put('/update_link')
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
'''