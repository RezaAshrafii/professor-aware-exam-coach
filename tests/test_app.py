from __future__ import annotations


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_course_workflow(client):
    response = client.post(
        "/courses",
        data={"name": "Probability 2", "professor": "Professor A", "daily_minutes": "90"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/courses/")

    page = client.get(location)
    assert page.status_code == 200
    assert "Probability 2" in page.text


def test_upload_and_demo_run(client):
    response = client.post("/courses", data={"name": "Regression", "daily_minutes": "90"}, follow_redirects=False)
    course_id = int(response.headers["location"].split("/")[-1])

    upload = client.post(
        f"/courses/{course_id}/sources",
        files={"file": ("notes.txt", "Linear regression assumes E(epsilon|X)=0.", "text/plain")},
        follow_redirects=False,
    )
    assert upload.status_code == 303

    run = client.post(
        f"/api/courses/{course_id}/run",
        json={"mode": "teach", "prompt": "فرض میانگین شرطی صفر را توضیح بده"},
    )
    assert run.status_code == 200
    payload = run.json()
    assert payload["provider"] == "demo"
    assert payload["evidence"]


def test_confirmed_mistake_can_be_saved_from_structured_report(client):
    response = client.post(
        "/courses",
        data={"name": "Probability 2", "daily_minutes": "90"},
        follow_redirects=False,
    )
    course_id = int(response.headers["location"].split("/")[-1])

    saved = client.post(
        f"/api/courses/{course_id}/mistakes",
        json={
            "topic": "Conditional probability",
            "category": "missing assumption",
            "description": "The conditioning event was not defined.",
            "prevention": "Define events before applying the formula.",
            "severity": "high",
        },
    )
    assert saved.status_code == 201
    assert saved.json()["status"] == "saved"

    page = client.get(f"/courses/{course_id}#mistakes")
    assert "The conditioning event was not defined." in page.text
