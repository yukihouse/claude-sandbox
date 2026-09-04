import pytest

from app import FAST_COMMENTS, MILESTONE_COMMENTS, SLOW_COMMENTS, app


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


def test_react_milestone_returns_milestone_comment(client):
    response = client.post("/api/react", json={"count": 10, "intervalMs": None})

    assert response.status_code == 200
    comment = response.get_json()["comment"]
    assert comment in [template.format(count=10) for template in MILESTONE_COMMENTS]


def test_react_fast_click_returns_fast_comment(client):
    response = client.post("/api/react", json={"count": 3, "intervalMs": 100})

    assert response.get_json()["comment"] in FAST_COMMENTS


def test_react_slow_click_returns_slow_comment(client):
    response = client.post("/api/react", json={"count": 3, "intervalMs": 5000})

    assert response.get_json()["comment"] in SLOW_COMMENTS


def test_react_missing_count_returns_400(client):
    response = client.post("/api/react", json={})

    assert response.status_code == 400
