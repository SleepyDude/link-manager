# import pytest
# import os
# import moto
# import boto3

# TABLE_NAME = 'TestLM'

# @pytest.fixture
# def lambda_environment():
#     os.environ['TABLE_NAME'] = TABLE_NAME

# @pytest.fixture
# def data_table():
#     with moto.mock_dynamodb():
#         client = boto3.client('dynamodb')
#         client.create_table(
#             AttributeDefinitions=[
#                 {'AttributeName': 'PK', 'AttributeType': 'S'},
#                 {'AttributeName': 'SK', 'AttributeType': 'S'},
#             ],
#             TableName=TABLE_NAME,
#             KeySchema=[
#                 {'AttributeName': 'PK', 'KeyType': 'HASH'},
#                 {'AttributeName': 'SK', 'KeyType': 'RANGE'},
#             ],
#             BillingMode='PAY_PER_REQUEST',
#         )
#         yield TABLE_NAME
