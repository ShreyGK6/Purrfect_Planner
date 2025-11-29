from datetime import datetime

def test_dashboard_requires_login(client):
    resp = client.get("/", follow_redirects=True)
    assert b"login" in resp.data.lower()


def test_add_pet_success(auth, client):
    auth.login()
    resp = client.post(
        "/add_pet",
        data={"name": "Snowy", "species": "cat"},
        follow_redirects=True,
    )
    assert b"Pet added successfully" in resp.data


def test_add_pet_missing_fields(auth, client):
    auth.login()
    resp = client.post("/add_pet", data={"name": ""}, follow_redirects=True)
    assert b"required" in resp.data.lower()


def test_add_task_success(auth, client, pet):
    auth.login()
    resp = client.post(
        "/add_task",
        data={
            "pet_id": pet.id,
            "title": "Walk",
            "desc": "Long walk",
            "date": "2025-01-01T12:00",
            "repeat": "None",
        },
        follow_redirects=True,
    )
    assert b"Task created successfully" in resp.data


def test_add_task_missing_fields(auth, client, pet):
    auth.login()
    resp = client.post(
        "/add_task",
        data={"pet_id": pet.id, "title": ""},
        follow_redirects=True,
    )
    assert b"required" in resp.data.lower()


def test_edit_task_updates_fields(auth, client, task):
    auth.login()
    resp = client.post(
        f"/edit_task/{task.id}",
        data={
            "pet_id": task.pet_id,
            "title": "Updated",
            "desc": "Updated desc",
            "date": "2025-01-01T13:00",
            "repeat": "None",
        },
        follow_redirects=True,
    )
    assert b"Task updated successfully" in resp.data


def test_delete_task(auth, client, task):
    auth.login()
    resp = client.post(f"/delete_task/{task.id}", follow_redirects=True)
    assert b"Task deleted" in resp.data
