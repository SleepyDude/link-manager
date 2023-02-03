import os
from typing import Optional, List
from pydantic import parse_obj_as
from pprint import pprint as pp
from datetime import datetime
from decimal import Decimal
import urllib.parse

try:
    import boto3
    from boto3.dynamodb.conditions import Key
    from boto3.dynamodb import conditions
    from botocore.exceptions import ClientError
except:
    pass

from .models.user_mod import UserInDB, User
from .models.link_mod import Link, LinkListParams, LinkInp, LinkInDB
from .utils.crypto import filter_keyword as f_k

"""
    HELPERS
"""

def check_resp(func_name, resp):
    if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
        Exception(f"Can't execute <{func_name}> for some reason, details: {resp}")

"""
    OPERATIONS WITH TABLE
"""

def _get_table():
    table_name = os.environ.get('TABLE_NAME')
    return boto3.resource('dynamodb').Table(table_name)

"""
    LINKS
"""

def db_put_link(username: str, link_inp: LinkInp) -> Optional[Link]:
    table = _get_table()
    # timestamp = Decimal(f'{datetime.utcnow().timestamp():.4f}')
    created = datetime.utcnow().isoformat(timespec='seconds')
    link_dict = link_inp.dict()
    link_dict.update({
        'PK': f'USER#{f_k(username)}',
        'SK': f'LINK#{created}',
        'created': created,
        'icon': None,
        'tags': [],
        'GSI1PK': f'USER#{f_k(username)}',
        'GSI1SK': f'LINK#{link_inp.url}',
    })
    resp = table.put_item(Item=link_dict)
    check_resp('db_put_link', resp)
    return Link(**link_dict)

def db_get_links_by_user(username: str,
    limit: int = None, offset: str = "") -> Optional[Link]:
    """
    Get links sorted by creation date in reverse order
    You can specify desired number of items and the offset
    datetime from which we should pick items
    By default the function pick all items from the last one

    `offset` - utc datetime in ISO format with seconds precision.
    `2023-01-13T10:32:24` for example
    `limit` - max number of items to get
    """
    SK_end = f'LINK#{offset}'
    if not offset:
        SK_end = 'LINL#'
    kwargs = dict()
    kwargs['ScanIndexForward'] = False
    kwargs['KeyConditionExpression'] =\
        'PK = :PK_val AND SK BETWEEN :SK_start AND :SK_end'
    kwargs['ExpressionAttributeValues'] = {
        ':PK_val': f'USER#{f_k(username)}',
        ':SK_start': f'LINK#',
        ':SK_end': SK_end,
    }
    if limit:
        kwargs['Limit'] = limit
    table = _get_table()
    resp = table.query(**kwargs)
    check_resp('db_get_links_by_user', resp)
    items = resp['Items']
    return parse_obj_as(List[Link], items)

def db_get_link_by_url(username: str, url: str):
    table = _get_table()
    resp = table.query(
        IndexName='GSI1-index',
        KeyConditionExpression='GSI1PK = :PK_val AND begins_with (GSI1SK, :SK_begins)',
        ExpressionAttributeValues={
            ':PK_val': f'USER#{f_k(username)}',
            ':SK_begins': f'LINK#{url}'
        }
    )
    check_resp('db_get_link_by_url', resp)
    items = resp['Items']
    return parse_obj_as(List[Link], items)

def db_get_link_by_id(username: str, id: str):
    '''
    `id` - timestamp in ISO format with seconds precision.

    `2023-01-13T10:32:24` for example
    '''
    table = _get_table()
    resp = table.get_item(Key={
        'PK': f'USER#{f_k(username)}',
        'SK': f'LINK#{id}',
    })
    check_resp('db_get_link_by_id', resp)
    item = resp.get('Item')
    if item is None:
        return None
    return parse_obj_as(Link, item)

'''
    TAGS
'''

def _db_add_tag_to_link(username: str, link_timestamp: str, tagname: str):
    table = _get_table()
    try:
        table.update_item(
            Key={
                'PK': f'USER#{f_k(username)}',
                'SK': f'LINK#{link_timestamp}',
            },
            UpdateExpression="SET #t = list_append(#t, :tag)",
            ExpressionAttributeNames={
                '#t': 'tags',
            },
            ExpressionAttributeValues={
                ':tag': [tagname],
                ':tagval': tagname,
            },
            ConditionExpression='not(contains(tags, :tagval))',
        )
    except ClientError as err:
        if err.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # raise ValueError(f'The tag {tagname} already exists') from err
            return {'Message': f'The tag {tagname} already exists'}
        else:
            raise err
    return None

def db_delete_tag(username: str, link_timestamp: str, tagname: str):
    table = _get_table()
    # firstly get tags to find id (because it's only possible to delete by id)
    resp = table.get_item(
        Key={
            'PK': f'USER#{f_k(username)}',
            'SK': f'LINK#{link_timestamp}',
        },
        AttributesToGet=['tags'],
    )
    check_resp('_db_delete_tag_from_link(part1)', resp)
    tags: list = resp['Item']['tags']
    try:
        index = tags.index(tagname)
    except ValueError:
        return None # no need to delete
    # let's delete tag by id from link entity
    try:
        table.update_item(
            Key={
                'PK': f'USER#{f_k(username)}',
                'SK': f'LINK#{link_timestamp}',
            },
            UpdateExpression=f"REMOVE #t[{index}]",
            ExpressionAttributeNames={
                '#t': 'tags',
            },
            ConditionExpression=conditions.Attr("PK").exists(),
        )
    except ClientError as err:
        if err.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ValueError(f'The tag {tagname} already exists') from err
        else:
            raise err
    
    # let's delete tag by id from all tags entities
    for tag in tags:
        if tag == tagname: # skip if its tag we want to delete
            continue
        try:
            table.update_item(
                Key={
                    'PK': f'USER#{f_k(username)}',
                    'SK': f'TAG#{tag}#{link_timestamp}',
                },
                UpdateExpression=f"REMOVE #t[{index}]",
                ExpressionAttributeNames={
                    '#t': 'tags',
                },
                ConditionExpression=conditions.Attr("PK").exists(),
            )
        except ClientError as err:
            if err.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f'The tag {tagname} already exists') from err
            else:
                raise err
    # lets delete a tag entity now
    table.delete_item(Key={
        'PK': f'USER#{f_k(username)}',
        'SK': f'TAG#{tagname}#{link_timestamp}',
    })

def db_delete_link(username: str, link_timestamp: str):
    table = _get_table()
    # find the link by link_timestamp
    resp = table.get_item(
        Key={
            'PK': f'USER#{f_k(username)}',
            'SK': f'LINK#{link_timestamp}',
        },
        AttributesToGet=['tags'],
    )
    check_resp('db_delete_link', resp)
    tags: list = resp['Item']['tags']
    # delete link
    table.delete_item(Key={
        'PK': f'USER#{f_k(username)}',
        'SK': f'LINK#{link_timestamp}', 
    })
    # delete tag entities
    with table.batch_writer() as batch:
        for tag in tags:
            batch.delete_item(Key={
                "PK": f'USER#{f_k(username)}',
                "SK": f'TAG#{tag}#{link_timestamp}'
            })

def _db_add_tag_to_tags(username: str, tagname: str, link: Link):
    '''
    link doesn't contain a new tag <tagname> yet
    '''
    # У линка уже есть какие-то теги, например ['a', 'b', 'c']
    # Значит существуют объекты, содержащие копию данного линка
    # С ключами:
    #   PK=USER#<username> SK=TAG#<a>#<link.created> 
    #   PK=USER#<username> SK=TAG#<b>#<link.created> 
    #   PK=USER#<username> SK=TAG#<c>#<link.created>
    # Им то и нужно добавить новый тег <tagname>
    table = _get_table()
    # print('link:', link)
    for tag in link.tags:
        try:
            table.update_item(
                Key={
                    'PK': f'USER#{f_k(username)}',
                    'SK': f'TAG#{tag}#{link.created}',
                },
                UpdateExpression="SET #t = list_append(#t, :l_tag)",
                ExpressionAttributeNames={
                    '#t': 'tags',
                },
                ExpressionAttributeValues={
                    ':tag': tagname,
                    ':l_tag': [tagname],
                },
                ConditionExpression='not(contains(tags, :tag))',
            )
        except ClientError as err:
            if err.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f'The tag {tagname} already exists in tag entity') from err
            else:
                raise err

def _db_create_tag_entity(username: str, tagname: str, link: Link):
    '''
    `link` entity contains old tags, so we should add a new one <tagname>

    TAG# entity should be able to provide the following queries:
    - Find all links for specific tags
    - Find all tags for specific link
    '''
    link.tags.append(tagname) # add a new tag
    table = _get_table()
    link_dict = link.dict()
    link_dict.update({
        'PK': f'USER#{f_k(username)}',
        'SK': f'TAG#{tagname}#{link.created}',
        # 'GSI1PK': f'LINK#{link.created}#{tagname}',
        # 'GSI1SK': f'LINK#{link.created}#{tagname}', # For reverse query
    })
    resp = table.put_item(Item=link_dict)
    check_resp('_db_create_tag_entity', resp)
    return None

def db_put_tag(username: str, link_timestamp: str, tagname: str):
    # find existing link firstly
    link = db_get_link_by_id(username, link_timestamp)
    if not link:
        raise ValueError('Link with this timestamp does not exist')
    # put tag to link entity
    _db_add_tag_to_link(username, link_timestamp, tagname)
    # put tag to TAG entities
    _db_add_tag_to_tags(username, tagname, link)
    # create tag entity
    _db_create_tag_entity(username, tagname, link)
    return None

def db_get_links_by_tag(username: str, tagname: str):
    table = _get_table()

    resp = table.query(
        KeyConditionExpression='PK = :PK_val AND begins_with (SK, :SK_begins)',
        ExpressionAttributeValues={
            ':PK_val': f'USER#{f_k(username)}',
            ':SK_begins': f'TAG#{tagname}#'
        }
    )
    check_resp('db_get_link_by_tag', resp)
    items = resp['Items']
    return parse_obj_as(List[Link], items)

"""
    USERS
"""

def db_put_user(user: UserInDB) -> None:
    '''
    Put User to db
    '''
    table = _get_table()
    # adding user entity
    user_dict = user.dict()
    user_dict.update({
        'PK': f'USER#{f_k(user.username)}',
        'SK': f'USER#{f_k(user.username)}',
    })
    resp = table.put_item(Item=user_dict)
    check_resp('db_put_user', resp)

def db_get_user(username: str) -> Optional[UserInDB]:
    '''
    Get User from db by username if exists, else None
    '''
    table = _get_table()
    resp = table.get_item(Key={
            'PK': f'USER#{f_k(username)}',
            'SK': f'USER#{f_k(username)}',
    })
    check_resp('db_get_user', resp)
    item = resp.get('Item')
    if item is None:
        return None
    return UserInDB(**item)

def db_delete_user(username: str) -> None:
    """
    Delete all entities related to the User
    """
    table = _get_table()
    # get all entities which belongs to the user
    resp = table.query(
        KeyConditionExpression='PK = :PK_val',
        ExpressionAttributeValues={
            ':PK_val': f'USER#{f_k(username)}',
        }
    )
    check_resp('db_delete_user', resp)
    items_to_delete = resp['Items']
    # let's delete all this items
    with table.batch_writer() as batch:
        for item in items_to_delete:
            resp = batch.delete_item(Key={
                'PK': item['PK'],
                'SK': item['SK'],
            })
    return None