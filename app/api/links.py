from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from ..models.link_mod import PutLinkRequest, Link, LinkListParams, LinkInp
from ..models.user_mod import User
from .users import get_current_user
from ..db import (
    db_get_links_by_user, db_put_link,
    db_get_link_by_url, db_get_link_by_id,
    _db_add_tag_to_link, _db_delete_tag_from_link
)

router = APIRouter()

@router.get('/get_my_links')
async def get_links(query: LinkListParams = Depends(), 
    cur_user: User = Depends(get_current_user)
):
    linklist: List[Link] = db_get_links_by_user(
        cur_user.username, query.limit, query.offset)
    return linklist

@router.get('/get_link_by_url')
async def get_link_by_url(
    url: str,
    cur_user: User = Depends(get_current_user)
):
    link = db_get_link_by_url(username=cur_user.username, url=url)
    return link

@router.get('/get_link_by_timestamp')
async def get_link_by_timestamp(
    timestamp: str,
    cur_user: User = Depends(get_current_user)
):
    link = db_get_link_by_id(username=cur_user.username, id=timestamp)
    return link

@router.post('/add_link')
async def add_link(link_inp: LinkInp, cur_user: User = Depends(get_current_user)):
    l = db_put_link(username=cur_user.username, link_inp=link_inp)
    return {'Message': l.dict()}

@router.post('/add_tag')
async def add_tag(link_timestamp: str, tagname: str,
    cur_user: User = Depends(get_current_user)
):
    err_msg = _db_add_tag_to_link(username=cur_user.username,
        link_timestamp=link_timestamp, tagname=tagname)
    if err_msg is not None:
        return err_msg
    return {'Message': 'Added tag'}

@router.delete('/remove_tag')
async def remove_tag(link_timestamp: str, tagname: str,
    cur_user: User = Depends(get_current_user)
):
    _db_delete_tag_from_link(cur_user.username,
        link_timestamp=link_timestamp, tagname=tagname)

'''
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