from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
from app.utils import get_password_hash


def test_root():
    resp = client.get('/')
    assert resp.status_code == 200

def test_hash():
    password = '12345'
    hashed_pass = get_password_hash(password)
    assert type(hashed_pass) == str

