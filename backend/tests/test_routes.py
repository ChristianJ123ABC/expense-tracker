#Resources
#https://flask.palletsprojects.com/en/stable/testing/


import pytest
import os
from dotenv import load_dotenv
load_dotenv(override=True)


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

def test_database_check(client):
    response = client.get("/database-check")
    assert response.status_code == 200