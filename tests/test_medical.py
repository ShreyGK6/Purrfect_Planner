def test_medical_records_view_uses_dummy_when_none(auth, client, pet):
    auth.login()
    resp = client.get(f"/records/{pet.id}")
    assert resp.status_code == 200
    assert b"Medical Records" in resp.data


def test_create_new_medical_record(auth, client, pet):
    auth.login()
    resp = client.post(
        f"/records/{pet.id}/edit",
        data={
            "vaccine": "Rabies",
            "allergies": "None",
            "medication": "Pill",
            "vet_info": "Clinic",
        },
        follow_redirects=True,
    )
    assert b"updated" in resp.data.lower()


def test_edit_existing_medical_record(auth, client, pet):
    auth.login()
    # first create
    client.post(
        f"/records/{pet.id}/edit",
        data={
            "vaccine": "Rabies",
            "allergies": "None",
            "medication": "Pill",
            "vet_info": "Clinic",
        },
        follow_redirects=True,
    )
    # now update
    resp = client.post(
        f"/records/{pet.id}/edit",
        data={
            "vaccine": "Updated",
            "allergies": "Dust",
            "medication": "New Med",
            "vet_info": "Updated Vet",
        },
        follow_redirects=True,
    )
    assert b"updated" in resp.data.lower()


def test_clear_medical_record(auth, client, pet):
    auth.login()
    # create record
    client.post(
        f"/records/{pet.id}/edit",
        data={
            "vaccine": "A",
            "allergies": "B",
            "medication": "C",
            "vet_info": "D",
        },
        follow_redirects=True,
    )
    # clear
    resp = client.post(f"/records/{pet.id}/clear", follow_redirects=True)
    assert b"cleared" in resp.data.lower()
