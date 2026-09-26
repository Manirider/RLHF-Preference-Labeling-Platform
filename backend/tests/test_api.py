import json
import os
import tempfile

from app.models.models import Pair

from downstream.validate_data import validate_jsonl_file


def test_health(client):
    """GET /api/health returns 200 with healthy database status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database"] == "healthy"

def test_pair_next_success(client):
    """GET /api/pairs/next?annotator_id=user1 returns 200 with pair fields."""
    res = client.get("/api/pairs/next?annotator_id=user1")
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert "prompt" in data
    assert "response_a" in data
    assert "response_b" in data
    assert "category" in data

def test_pair_next_empty_annotator(client):
    """GET /api/pairs/next with empty annotator_id returns 400."""
    res = client.get("/api/pairs/next?annotator_id=")
    assert res.status_code == 400

    res_spaces = client.get("/api/pairs/next?annotator_id=   ")
    assert res_spaces.status_code == 400

def test_annotator_isolation(client):
    """
    Test annotator isolation:
    When User A labels pair 1, User A gets pair 2 next.
    User B should still be able to get pair 1.
    """
    res1 = client.get("/api/pairs/next?annotator_id=alice")
    assert res1.status_code == 200
    pair1_id = res1.json()["id"]

    # Alice labels pair 1
    post_res = client.post("/api/labels", json={
        "pair_id": pair1_id,
        "annotator_id": "alice",
        "chosen": "A"
    })
    assert post_res.status_code == 201

    # Alice gets next pair, should NOT be pair 1
    res2 = client.get("/api/pairs/next?annotator_id=alice")
    assert res2.status_code == 200
    assert res2.json()["id"] != pair1_id

    # Bob asks for next pair; Bob should receive pair 1
    res_bob = client.get("/api/pairs/next?annotator_id=bob")
    assert res_bob.status_code == 200
    assert res_bob.json()["id"] == pair1_id

def test_label_submission_all_choices(client):
    """Test submitting all allowed choices: A, B, tie, skip."""
    choices = ["A", "B", "tie", "skip"]
    for i, choice in enumerate(choices, start=1):
        res = client.post("/api/labels", json={
            "pair_id": i,
            "annotator_id": f"annotator_{choice}",
            "chosen": choice
        })
        assert res.status_code == 201
        assert "id" in res.json()

def test_label_submission_invalid_choice(client):
    """Submitting an invalid preference choice returns 400/422."""
    res = client.post("/api/labels", json={
        "pair_id": 1,
        "annotator_id": "charlie",
        "chosen": "invalid_choice"
    })
    assert res.status_code in (400, 422)

def test_label_submission_nonexistent_pair(client):
    """Submitting a label for a non-existent pair returns 404."""
    res = client.post("/api/labels", json={
        "pair_id": 999999,
        "annotator_id": "charlie",
        "chosen": "A"
    })
    assert res.status_code == 404

def test_duplicate_label_conflict(client):
    """Submitting duplicate annotation from the same annotator for the same pair returns 409."""
    payload = {
        "pair_id": 1,
        "annotator_id": "dave",
        "chosen": "A"
    }
    first = client.post("/api/labels", json=payload)
    assert first.status_code == 201

    second = client.post("/api/labels", json=payload)
    assert second.status_code == 409
    assert "Already labeled" in second.json()["detail"]

def test_all_pairs_labeled_returns_404(client, db_session):
    """After all pairs are labeled by an annotator, next returns 404."""
    pairs = db_session.query(Pair).all()
    for p in pairs:
        client.post("/api/labels", json={
            "pair_id": p.id,
            "annotator_id": "completionist",
            "chosen": "A"
        })

    res = client.get("/api/pairs/next?annotator_id=completionist")
    assert res.status_code == 404
    assert res.json()["detail"] == "No unlabeled pairs available for this annotator."

def test_export_jsonl_format_and_mapping(client):
    """
    Test GET /api/export:
    - Headers: application/x-jsonlines, Content-Disposition
    - Valid JSON lines
    - If chosen == 'A', chosen text is response_a, rejected is response_b
    - If chosen == 'B', chosen text is response_b, rejected is response_a
    - Tie and skip are excluded from export
    """
    client.post("/api/labels", json={"pair_id": 1, "annotator_id": "u1", "chosen": "A"})
    client.post("/api/labels", json={"pair_id": 2, "annotator_id": "u1", "chosen": "B"})
    client.post("/api/labels", json={"pair_id": 3, "annotator_id": "u1", "chosen": "tie"})
    client.post("/api/labels", json={"pair_id": 4, "annotator_id": "u1", "chosen": "skip"})

    res = client.get("/api/export")
    assert res.status_code == 200
    assert "application/x-jsonlines" in res.headers["Content-Type"]
    assert 'attachment; filename="labels.jsonl"' in res.headers["Content-Disposition"]

    lines = [line.strip() for line in res.text.strip().split("\n") if line.strip()]
    assert len(lines) == 2  # tie and skip must be excluded

    # Line 1: chosen A
    rec1 = json.loads(lines[0])
    assert "prompt" in rec1 and isinstance(rec1["prompt"], str)
    assert "chosen" in rec1 and isinstance(rec1["chosen"], str)
    assert "rejected" in rec1 and isinstance(rec1["rejected"], str)
    assert "metadata" in rec1
    assert rec1["chosen"] == "TCP is connection-oriented; UDP is connectionless."
    assert rec1["rejected"] == "TCP has 3-way handshakes; UDP streams packets without ACK."

    # Line 2: chosen B
    rec2 = json.loads(lines[1])
    assert rec2["chosen"] == "def reverse(head):\n    curr = head\n    prev = None\n    ..."
    assert rec2["rejected"] == "def reverse(head):\n    prev = None\n    curr = head\n    ..."

def test_export_category_filtering(client):
    """Test filtering export by category."""
    client.post("/api/labels", json={"pair_id": 1, "annotator_id": "u1", "chosen": "A"}) # factual_qa
    client.post("/api/labels", json={"pair_id": 2, "annotator_id": "u1", "chosen": "A"}) # code_generation

    # Filter for code_generation
    res = client.get("/api/export?category=code_generation")
    assert res.status_code == 200
    lines = [line for line in res.text.strip().split("\n") if line.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["metadata"]["category"] == "code_generation"

    # Filter for non-matching category
    res_empty = client.get("/api/export?category=non_existent_cat")
    assert res_empty.status_code == 200
    assert res_empty.text.strip() == ""

def test_analytics_exact_counts(client):
    """Test GET /api/analytics returns exact counts and all 4 keys."""
    # Initially zero
    res = client.get("/api/analytics")
    assert res.status_code == 200
    data = res.json()
    assert data["total_labels"] == 0
    assert data["label_distribution"] == {"A": 0, "B": 0, "tie": 0, "skip": 0}
    assert data["agreement_rate"] == 0.0

    # Add 2 A, 1 B, 1 tie, 1 skip
    client.post("/api/labels", json={"pair_id": 1, "annotator_id": "u1", "chosen": "A"})
    client.post("/api/labels", json={"pair_id": 2, "annotator_id": "u1", "chosen": "A"})
    client.post("/api/labels", json={"pair_id": 3, "annotator_id": "u1", "chosen": "B"})
    client.post("/api/labels", json={"pair_id": 4, "annotator_id": "u1", "chosen": "tie"})
    client.post("/api/labels", json={"pair_id": 5, "annotator_id": "u1", "chosen": "skip"})

    res2 = client.get("/api/analytics")
    data2 = res2.json()
    assert data2["total_labels"] == 5
    assert data2["label_distribution"]["A"] == 2
    assert data2["label_distribution"]["B"] == 1
    assert data2["label_distribution"]["tie"] == 1
    assert data2["label_distribution"]["skip"] == 1

def test_agreement_metric_identical_labeling(client):
    """
    When multiple annotators label the same pair with the exact same choice,
    agreement_rate must equal 1.0.
    """
    for user in ("ann_1", "ann_2", "ann_3"):
        client.post("/api/labels", json={"pair_id": 1, "annotator_id": user, "chosen": "A"})

    res = client.get("/api/analytics")
    data = res.json()
    assert data["agreement_rate"] == 1.0

def test_agreement_metric_mixed_labeling(client):
    """
    When 2 annotators vote A and 1 votes B for a pair:
    majority is 2, total is 3 -> agreement_rate = 2/3 = 0.6667.
    """
    client.post("/api/labels", json={"pair_id": 1, "annotator_id": "u1", "chosen": "A"})
    client.post("/api/labels", json={"pair_id": 1, "annotator_id": "u2", "chosen": "A"})
    client.post("/api/labels", json={"pair_id": 1, "annotator_id": "u3", "chosen": "B"})

    res = client.get("/api/analytics")
    data = res.json()
    assert round(data["agreement_rate"], 2) == 0.67

def test_downstream_validator_script(client):
    """Test downstream validator against valid exported data and invalid data."""
    client.post("/api/labels", json={"pair_id": 1, "annotator_id": "v1", "chosen": "A"})
    client.post("/api/labels", json={"pair_id": 2, "annotator_id": "v1", "chosen": "B"})

    res = client.get("/api/export")
    assert res.status_code == 200

    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".jsonl", encoding="utf-8") as tf:
        tf.write(res.text)
        valid_path = tf.name

    try:
        assert validate_jsonl_file(valid_path) is True
    finally:
        os.remove(valid_path)

    # Test invalid JSONL
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".jsonl", encoding="utf-8") as tf:
        tf.write('{"prompt": "Missing chosen and rejected"}\n')
        invalid_path = tf.name

    try:
        assert validate_jsonl_file(invalid_path) is False
    finally:
        os.remove(invalid_path)
