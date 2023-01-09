import os
from typing import Optional, List
from pydantic import parse_obj_as
from pprint import pprint as pp

try:
    import boto3
except:
    pass

from .models.user_mod import UserInDB
from .models.link_mod import LinkList

"""
    OPERATIONS WITH TABLE
"""

def _get_table():
    table_name = os.environ.get('TABLE_NAME')
    return boto3.resource('dynamodb').Table(table_name)

"""
    USERS
"""

def get_db_user(username: str) -> Optional[UserInDB]:
    """
    Get user from database by username if exists, else None
    """
    table = _get_table()
    resp = table.get_item(Key={
            'PK': f'USER#{username.lower()}',
            'SK': f'USER#{username.lower()}',
    })
    item = resp.get('Item')
    if item is None:
        return None
    return UserInDB(**item)


def put_db_link_list(username: str, listname: str):
    listname_escape = listname.replace(' ', '_')
    table = _get_table()
    resp = table.put_item(Item={
        'PK': f'USER#{username.lower()}',
        'SK': f'LLIST#{listname_escape}',
        'Type': 'LinkList',
        'Listname': listname,
        'LastAdd': None,
        'Elements': 0,
    })
    if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception(f"Can't put <link list> for some reason, details: {resp}")
    return None

def get_user_link_lists(username: str):
    table = _get_table()
    resp = table.query(
        KeyConditionExpression='PK = :PK_val AND begins_with (SK, :SK_begin)',
        ExpressionAttributeValues={
            ':PK_val': f'USER#{username.lower()}',
            ':SK_begin': f'LLIST#'
        }
    )
    if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception('Something wrong with <get_user_link_lists> with resp:'
        , resp)
    items = resp['Items']
    return parse_obj_as(List[LinkList], items)

def db_delete_user(username: str):
    table = _get_table()
    # get all entities which belongs to the user
    resp = table.query(
        KeyConditionExpression='PK = :PK_val',
        ExpressionAttributeValues={
            ':PK_val': f'USER#{username.lower()}',
        }
    )
    if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception('Something wrong with <db_delete_user> with resp:'
        , resp)
    items_to_delete = resp['Items']
    # let's delete all this items
    with table.batch_writer() as batch:
        for item in items_to_delete:
            resp = batch.delete_item(Key={
                'PK': item['PK'],
                'SK': item['SK'],
            })
    return None

# pattern: Add a new user
# Should also create 2 empty link lists
def put_db_user(user: UserInDB) -> None:
    """
    Put user in database, doesn't check if user is already
    exists.

    Access Pattern: `add a new user`

    Also add 2 empty link lists tied with the user.
    """
    table = _get_table()
    # adding user entity
    item = user.dict()
    item.update({
        'PK': f'USER#{user.Username.lower()}',
        'SK': f'USER#{user.Username.lower()}',
        'Type': 'User',
    })
    resp = table.put_item(Item=item)
    if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception(f"Can't put <user> for some reason, details: {resp}")
    # adding link list entity
    put_db_link_list(user.Username, 'All links')
    put_db_link_list(user.Username, 'Trash bin')
    return None

def get_user_rules(username: str):
    '''
    Get all link list rules of user
    '''
    table = _get_table()
    resp = table.query(
        KeyConditionExpression='PK = :PK_val',
        ExpressionAttributeValues={
            ':PK_val': f'ULRULE#{username.lower()}'
        }
    )

def get_list_rules(username: str):
    '''
    Get all rules attached to a list
    '''
    table = _get_table()
    resp = table.query(
        KeyConditionExpression='PK = :PK_val',
        ExpressionAttributeValues={
            ':PK_val': f'ULRULE#{username.lower()}'
        }
    )

