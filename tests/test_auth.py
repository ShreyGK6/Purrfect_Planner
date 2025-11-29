def test_register_new_user(client):
    resp = client.post(
        "/register",
        data={"username": "newuser", "email": "new@a.com", "password": "abc"},
        follow_redirects=True,
    )
    assert b"Account created successfully" in resp.data


def test_register_requires_all_fields(client):
    resp = client.post("/register", data={}, follow_redirects=True)
    assert b"All fields are required" in resp.data


def test_register_duplicate_username(client, _user):
    resp = client.post(
        "/register",
        data={"username": "testuser", "email": "a@b.com", "password": "123"},
        follow_redirects=True,
    )
    assert b"already exists" in resp.data


def test_login_valid(auth):
    resp = auth.login()
    assert b"Welcome back" in resp.data


def test_login_invalid_credentials(client):
    resp = client.post("/login", data={"username": "x", "password": "y"}, follow_redirects=True)
    assert b"Invalid login" in resp.data


def test_logout(auth):
    auth.login()
    resp = auth.logout()
    assert b"logged out" in resp.data.lower()
