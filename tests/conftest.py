import os
import pytest
from types import SimpleNamespace
from datetime import datetime

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from purrfectplanner.app import create_app
from purrfectplanner.models import db, User, Pet, Task, MedicalRecord


@pytest.fixture
def app():
    app = create_app()

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def _user(app):
    u = User(username="testuser", email="test@example.com")
    u.set_password("password123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def auth(client, _user):
    def login(username="testuser", password="password123"):
        return client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def logout():
        return client.get("/logout", follow_redirects=True)

    return SimpleNamespace(login=login, logout=logout)


@pytest.fixture
def pet(app, _user):
    p = Pet(name="Mochi", type="cat", owner_id=_user.id, photo_path="")
    db.session.add(p)
    db.session.commit()
    return p


@pytest.fixture
def task(app, pet):
    t = Task(
        pet_id=pet.id,
        title="Feed Mochi",
        desc="Wet food",
        repeat="None",
        date=datetime(2025, 1, 1, 12, 0)
    )
    db.session.add(t)
    db.session.commit()
    return t
