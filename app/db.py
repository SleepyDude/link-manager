import os
from typing import Optional

try:
    import boto3
except:
    pass

from .models.user_mod import UserInDB

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

def put_db_user(user: UserInDB) -> None:
    """
    Put user in database
    """
    table = _get_table()

    item = user.dict()
    item.update({
        'PK': f'USER#{user.Username.lower()}',
        'SK': f'USER#{user.Username.lower()}',
        'Type': 'User',
    })
    resp = table.put_item(Item=item)
    if resp['ResponseMetadata']['HTTPStatusCode'] == 200:
        return None
    raise Exception(f"Can't put item for some reason, details: {resp}")