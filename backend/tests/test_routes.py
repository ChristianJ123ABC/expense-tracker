#Resources
#https://flask.palletsprojects.com/en/stable/testing/


import pytest
import os

os.environ.setdefault("MYSQL_HOST", "localhost")
os.environ.setdefault("MYSQL_USER", "test")
os.environ.setdefault("MYSQL_PASSWORD", "test")
os.environ.setdefault("MYSQL_DB", "test")
os.environ.setdefault("MYSQL_PORT", "3306")
os.environ.setdefault("MYSQL_CHARSET", "utf8mb4")

from server import app as create_app

@pytest.fixture()
def app():
    create_app.config.update({
        "TESTING": True,
        
    })
    yield create_app

@pytest.fixture()
def client(app):
    return app.test_client()


def test(client):
    response = client.get("/test")
    assert response.status_code == 200