import pytest
from app import app, db, User
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
  app.config['TESTING'] = True
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # in-memory database for tests
  with app.test_client() as client:
    with app.app_context():
      db.create_all()
    yield client
    with app.app_context():
      db.drop_all()

def test_homepage(client):
  response = client.get('/')
  assert response.status_code == 200

def test_register(client):
  response = client.post('/register', data={
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'Test1234'
  }, follow_redirects=True)
  assert b"Registration successful" in response.data

def test_duplicate_email(client):
  hashed_pw = generate_password_hash("Test1234", method='pbkdf2:sha256')
  user = User(username="existinguser", email="test@example.com", password=hashed_pw)
  db.session.add(user)
  db.session.commit()

  response = client.post('/register', data={
    'username': 'newuser',
    'email': 'test@example.com',
    'password': 'Test1234'
  }, follow_redirects=True)
  assert b"Email is already registered" in response.data

def test_password_validation(client):
  response = client.post('/register', data={
    'username': 'badpassuser',
    'email': 'badpass@example.com',
    'password': '123'
  })
  assert b"Password must be at least 8 characters." in response.data
  assert b"Password must contain at least one letter and one number." in response.data