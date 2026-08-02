from __future__ import annotations


def create_course(client, name: str = "Statistical Learning") -> int:
    response = client.post(
        "/api/courses",
        json={
            "name": name,
            "professor": "Professor A",
            "term": "1405-1",
            "exam_date": "2026-12-20",
            "target_grade": 18.5,
            "daily_minutes": 120,
            "exam_scope": "Chapters 1-4",
            "notes": "",
        },
    )
    assert response.status_code == 201
    return int(response.json()["course"]["id"])


def test_product_api_course_workspace(client):
    course_id = create_course(client)

    listing = client.get("/api/courses")
    assert listing.status_code == 200
    assert listing.json()["items"][0]["name"] == "Statistical Learning"

    workspace = client.get(f"/api/courses/{course_id}")
    assert workspace.status_code == 200
    assert workspace.json()["course"]["target_grade"] == 18.5
    assert workspace.json()["sources"] == []
    assert workspace.json()["example_cards"] == []

    updated = client.put(
        f"/api/courses/{course_id}",
        json={
            "name": "Statistical Learning I",
            "professor": "Professor B",
            "term": "1405-1",
            "exam_date": "2026-12-21",
            "target_grade": 19,
            "daily_minutes": 100,
            "exam_scope": "All lectures",
            "notes": "Updated from Next UI",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["course"]["name"] == "Statistical Learning I"


def test_product_api_source_example_and_mistake_crud(client):
    course_id = create_course(client, "Probability 2")

    upload = client.post(
        f"/api/courses/{course_id}/sources",
        files={"file": ("lecture.txt", "Bayes theorem example from class", "text/plain")},
    )
    assert upload.status_code == 201
    source = upload.json()["source"]
    assert source["filename"] == "lecture.txt"
    assert "stored_path" not in source
    assert source["chunk_count"] == 1

    example = client.post(
        f"/api/courses/{course_id}/example-cards",
        json={
            "title": "Bayes class example",
            "topic": "Conditional probability",
            "question": "Find P(A|B).",
            "solution": "Define events, then apply Bayes theorem.",
            "method_name": "Bayes theorem",
            "source_kind": "cleaned_transcript",
            "source_reference": "Session 4",
            "notes": "Use professor notation.",
            "status": "draft",
        },
    )
    assert example.status_code == 201
    card_id = example.json()["example_card"]["id"]

    confirmed = client.patch(
        f"/api/courses/{course_id}/example-cards/{card_id}",
        json={"status": "confirmed"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["example_card"]["status"] == "confirmed"

    mistake = client.post(
        f"/api/courses/{course_id}/mistakes",
        json={
            "topic": "Bayes",
            "category": "missing definition",
            "description": "Events were not defined.",
            "prevention": "Define events before the formula.",
            "severity": "high",
        },
    )
    assert mistake.status_code == 201
    mistake_id = mistake.json()["mistake"]["id"]

    assert client.delete(f"/api/courses/{course_id}/mistakes/{mistake_id}").status_code == 204
    assert client.delete(f"/api/courses/{course_id}/example-cards/{card_id}").status_code == 204
    assert client.delete(f"/api/sources/{source['id']}").status_code == 204


def test_product_api_course_isolation(client):
    first_id = create_course(client, "Course A")
    second_id = create_course(client, "Course B")
    example = client.post(
        f"/api/courses/{first_id}/example-cards",
        json={
            "title": "Private method",
            "question": "Question",
            "solution": "Solution",
            "status": "draft",
        },
    ).json()["example_card"]

    response = client.patch(
        f"/api/courses/{second_id}/example-cards/{example['id']}",
        json={"status": "confirmed"},
    )
    assert response.status_code == 404


def test_cors_allows_local_next_frontend(client):
    response = client.options(
        "/api/courses",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
