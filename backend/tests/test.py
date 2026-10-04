#Resources
#https://flask.palletsprojects.com/en/stable/testing/


import pytest
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