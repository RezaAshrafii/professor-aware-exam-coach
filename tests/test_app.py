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


def test_example_card_is_used_only_after_confirmation(client):
    response = client.post(
        "/courses",
        data={"name": "Probability 2", "professor": "Professor A", "daily_minutes": "90"},
        follow_redirects=False,
    )
    course_id = int(response.headers["location"].split("/")[-1])

    created = client.post(
        f"/courses/{course_id}/example-cards",
        data={
            "title": "Bayes example from class",
            "topic": "Conditional probability",
            "question": "Find P(A|B).",
            "solution": "The professor defined both events and applied Bayes' theorem.",
            "method_name": "Bayes theorem",
            "source_kind": "cleaned_transcript",
            "source_reference": "Session 4, 00:18:40",
            "status": "draft",
        },
        follow_redirects=False,
    )
    assert created.status_code == 303

    page = client.get(f"/courses/{course_id}#examples")
    assert "Bayes example from class" in page.text
    assert "پیش‌نویس" in page.text

    draft_run = client.post(
        f"/api/courses/{course_id}/run",
        json={"mode": "teach", "prompt": "Explain the Bayes example from class"},
    )
    assert draft_run.status_code == 200
    assert draft_run.json()["evidence"] == []

    from app import repositories

    card_id = repositories.list_example_cards(course_id)[0]["id"]
    confirmed = client.post(
        f"/example-cards/{card_id}/status",
        data={"course_id": course_id, "status": "confirmed"},
        follow_redirects=False,
    )
    assert confirmed.status_code == 303

    confirmed_run = client.post(
        f"/api/courses/{course_id}/run",
        json={"mode": "teach", "prompt": "Explain the Bayes example from class"},
    )
    assert confirmed_run.status_code == 200
    evidence = confirmed_run.json()["evidence"]
    assert evidence
    assert evidence[0]["evidence_kind"] == "example_card"
    assert evidence[0]["filename"] == "کارت مثال: Bayes example from class"
    assert evidence[0]["chunk_index"] is None


def test_example_card_cannot_be_changed_from_another_course(client):
    first = client.post(
        "/courses", data={"name": "Course A", "daily_minutes": "90"}, follow_redirects=False
    )
    second = client.post(
        "/courses", data={"name": "Course B", "daily_minutes": "90"}, follow_redirects=False
    )
    first_id = int(first.headers["location"].split("/")[-1])
    second_id = int(second.headers["location"].split("/")[-1])

    client.post(
        f"/courses/{first_id}/example-cards",
        data={
            "title": "Private example",
            "question": "Question",
            "solution": "Solution",
            "status": "draft",
        },
    )

    from app import repositories

    card_id = repositories.list_example_cards(first_id)[0]["id"]
    response = client.post(
        f"/example-cards/{card_id}/status",
        data={"course_id": second_id, "status": "confirmed"},
    )
    assert response.status_code == 404
