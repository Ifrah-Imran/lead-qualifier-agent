import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from openai import APIError

from app.main import app


@pytest.fixture
def client():
    with patch("app.main.ensure_leads_table"):
        yield TestClient(app)


def _mock_openai_score_response(score: int = 8, confidence: str = "high", reason: str = "Strong fit."):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.tool_calls = [MagicMock()]
    mock_response.choices[0].message.tool_calls[0].function.arguments = json.dumps(
        {"score": score, "confidence": confidence, "reason": reason}
    )
    return mock_response


def test_score_returns_structured_result(client):
    with (
        patch("app.main.OPENAI_API_KEY", "test-key"),
        patch("app.main.retrieve_similar_examples", return_value=[]),
        patch("app.main.OpenAI") as mock_openai,
    ):
        mock_openai.return_value.chat.completions.create.return_value = _mock_openai_score_response()

        response = client.post(
            "/score",
            json={
                "name": "Ayesha Khan",
                "company": "FlowPilot",
                "title": "Founder",
                "company_size": "10-20",
                "industry": "B2B SaaS",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 8
    assert data["confidence"] == "high"
    assert data["reason"] == "Strong fit."


def test_score_rejects_invalid_company_size(client):
    with patch("app.main.OPENAI_API_KEY", "test-key"):
        response = client.post(
            "/score",
            json={
                "name": "Test User",
                "company": "Test Co",
                "company_size": "not-a-range",
            },
        )

    assert response.status_code == 422
    assert "Unrecognized company_size" in response.json()["detail"]


def test_score_openai_failure_returns_clear_error(client):
    with (
        patch("app.main.OPENAI_API_KEY", "test-key"),
        patch("app.main.retrieve_similar_examples", return_value=[]),
        patch("app.main.OpenAI") as mock_openai,
    ):
        mock_openai.return_value.chat.completions.create.side_effect = APIError(
            "Service unavailable",
            request=MagicMock(),
            body=None,
        )

        response = client.post(
            "/score",
            json={"name": "Test User", "company": "Test Co"},
        )

    assert response.status_code == 502
    assert "OpenAI" in response.json()["detail"]
