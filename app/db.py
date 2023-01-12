import os
from typing import Optional, List
from pydantic import parse_obj_as
from pprint import pprint as pp
from datetime import datetime
from decimal import Decimal

try:
    import boto3
except:
    pass

from .models.user_mod import UserInDB, User
from .models.link_mod import Link, LinkListParams, LinkInp, LinkInDB
from .utils import filter_keyword as f_k

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
    timestamp = Decimal(f'{datetime.utcnow().timestamp():.4f}')
    created = datetime.fromtimestamp(timestamp).isoformat()

    link_dict = link_inp.dict()
    link_dict.update({
        'PK': f'USER#{f_k(username)}',
        'SK': f'LINK#{timestamp}',
        'created': created,
        'priority_num': timestamp,
        'icon': None,
        'tags': [],
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

    `offset` - priority number (see priority number of other links)
    `limit` - number of items to get
    """
    kwargs = dict()
    kwargs['ScanIndexForward'] = False
    kwargs['KeyConditionExpression'] =\
        'PK = :PK_val AND SK BETWEEN :SK_start AND :SK_end'
    kwargs['ExpressionAttributeValues'] = {
        ':PK_val': f'USER#{f_k(username)}',
        ':SK_start': f'LINK#{offset}',
        ':SK_end': 'USER#'
    }
    if limit:
        kwargs['Limit'] = limit

    print('have the following kwargs:', kwargs)
    table = _get_table()
    resp = table.query(**kwargs)
    check_resp('db_get_links_by_user', resp)
    items = resp['Items']
    return parse_obj_as(List[Link], items)


# def put_db_link_list(username: str, listname: str):
#     listname_escape = listname.replace(' ', '_')
#     table = _get_table()
#     resp = table.put_item(Item={
#         'PK': f'USER#{username.lower()}',
#         'SK': f'LLIST#{listname_escape}',
#         'Type': 'LinkList',
#         'Listname': listname,
#         'LastAdd': None,
#         'Elements': 0,
#     })
#     if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
#         raise Exception(f"Can't put <link list> for some reason, details: {resp}")
#     return None

# def get_user_link_lists(username: str):
#     table = _get_table()
#     resp = table.query(
#         KeyConditionExpression='PK = :PK_val AND begins_with (SK, :SK_begin)',
#         ExpressionAttributeValues={
#             ':PK_val': f'USER#{username.lower()}',
#             ':SK_begin': f'LLIST#'
#         }
#     )
#     if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
#         raise Exception('Something wrong with <get_user_link_lists> with resp:'
#         , resp)
#     items = resp['Items']
#     return parse_obj_as(List[LinkList], items)

# def get_user_rules(username: str):
#     '''
#     Get all link list rules of user
#     '''
#     table = _get_table()
#     resp = table.query(
#         KeyConditionExpression='PK = :PK_val',
#         ExpressionAttributeValues={
#             ':PK_val': f'ULRULE#{username.lower()}'
#         }
#     )

# def get_list_rules(username: str):
#     '''
#     Get all rules attached to a list
#     '''
#     table = _get_table()
#     resp = table.query(
#         KeyConditionExpression='PK = :PK_val',
#         ExpressionAttributeValues={
#             ':PK_val': f'ULRULE#{username.lower()}'
#         }
#     )

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