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
    db_put_tag, db_delete_tag,
    db_get_links_by_tag
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
    try:
        db_put_tag(username=cur_user.username,
            link_timestamp=link_timestamp, tagname=tagname)
    except Exception as e:
        return {'Message': 'Cant add a tag', 'details': str(e)}
    return {'Message': 'Tag added'}

@router.delete('/remove_tag')
async def remove_tag(link_timestamp: str, tagname: str,
    cur_user: User = Depends(get_current_user)
):
    db_delete_tag(cur_user.username,
        link_timestamp=link_timestamp, tagname=tagname)

@router.get('/get_links_by_tag')
async def get_links_by_tag(tagname: str,
    cur_user: User = Depends(get_current_user)
):
    try:
        links = db_get_links_by_tag(cur_user.username, tagname)
        return links
    except:
        pass
    return {'Message': 'something went wrong'}