import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_returns_ok(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_renders_counter_page(client):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert "カウンターデモ (Python版)" in body
    assert 'id="count"' in body
