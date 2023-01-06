import os
try:
    import boto3
    from boto3.dynamodb.conditions import Key
except:
    pass

def _get_table():
    table_name = os.environ.get('TABLE_NAME')
    return boto3.resource('dynamodb').Table(table_name)