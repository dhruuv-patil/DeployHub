import pytest
from app import app, init_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

def test_health_check(client):
    """Test that the health endpoint returns HTTP 200 and healthy status."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'DeployHub'
    assert 'database' in data
    assert 'timestamp' in data

def test_info_endpoint(client):
    """Test that the project info endpoint returns correct project metadata."""
    response = client.get('/api/info')
    assert response.status_code == 200
    data = response.get_json()
    assert data['app_name'] == 'DeployHub'
    assert data['author'] == 'Dhruv Patil'
    assert data['github_repo'] == 'https://github.com/dhruuv-patil/DeployHub'
    assert 'architecture' in data

def test_index_page(client):
    """Test that the homepage renders successfully."""
    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert 'DeployHub' in html

def test_submit_message_form(client):
    """Test submitting a new message via standard form-data."""
    response = client.post('/submit', data={'new_message': 'CI/CD Pipeline Test Message'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['message'] == 'CI/CD Pipeline Test Message'
    assert 'created_at' in data

def test_submit_message_json(client):
    """Test submitting a new message via JSON payload."""
    response = client.post('/submit', json={'new_message': 'Automated JSON Test Message'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['message'] == 'Automated JSON Test Message'

def test_submit_empty_message(client):
    """Test that submitting an empty message is rejected with 400 Bad Request."""
    response = client.post('/submit', data={'new_message': '   '})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_submit_message_exceeding_length(client):
    """Test that submitting a message longer than 500 characters is rejected."""
    long_message = 'A' * 501
    response = client.post('/submit', json={'new_message': long_message})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_get_messages_api(client):
    """Test retrieving messages via the REST API endpoint."""
    client.post('/submit', json={'new_message': 'Message for API fetch'})
    response = client.get('/api/messages')
    assert response.status_code == 200
    data = response.get_json()
    assert 'messages' in data
    assert 'count' in data
    assert data['count'] >= 1
    messages_text = [m['message'] for m in data['messages']]
    assert 'Message for API fetch' in messages_text

def test_clear_messages_api(client):
    """Test clearing all messages via the REST API."""
    client.post('/submit', json={'new_message': 'Temp message'})
    clear_resp = client.post('/api/clear')
    assert clear_resp.status_code == 200

    list_resp = client.get('/api/messages')
    assert list_resp.status_code == 200
    assert list_resp.get_json()['count'] == 0
