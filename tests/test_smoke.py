from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_works():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "FastAPI Calculator" in resp.text
