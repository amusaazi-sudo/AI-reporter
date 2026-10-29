from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from openai import APIError, APITimeoutError

import ai_prompt
import ai_reporter


def fake_response(json_data):
    """Build a fake requests response that returns json_data."""
    response = MagicMock()
    response.json.return_value = json_data
    response.raise_for_status.return_value = None
    return response


GEOCODING_RESPONSE = {
    "results": [
        {"name": "Kampala", "country": "Uganda", "latitude": 0.31, "longitude": 32.58}
    ]
}

FORECAST_RESPONSE = {
    "current": {
        "time": "2026-10-29T18:00",
        "temperature_2m": 26.3,
        "apparent_temperature": 27.1,
        "relative_humidity_2m": 59,
        "precipitation": 0.0,
        "wind_speed_10m": 2.7,
    },
    "current_units": {
        "temperature_2m": "°C",
        "apparent_temperature": "°C",
        "relative_humidity_2m": "%",
        "precipitation": "mm",
        "wind_speed_10m": "km/h",
    },
    "elevation": 1200,  # extra field that should not be sent to the AI
}


# ---------- Input validation ----------


def test_validate_email_valid():
    assert ai_reporter.validate_email("test@gmail.com") is True


@pytest.mark.parametrize(
    "email", ["testgmail.com", "test@", "@gmail.com", "a b@gmail.com"]
)
def test_validate_email_invalid(email):
    assert ai_reporter.validate_email(email) is False


def test_validate_report_type_valid():
    assert ai_reporter.validate_report_type("weather") is True
    assert ai_reporter.validate_report_type("news_summary") is True


def test_validate_report_type_invalid():
    assert ai_reporter.validate_report_type("sports") is False


def test_missing_env_variable_raises(monkeypatch):
    monkeypatch.delenv("NEWS_API_KEY", raising=False)
    with pytest.raises(ValueError, match="NEWS_API_KEY"):
        ai_reporter.require_env("NEWS_API_KEY")


def test_placeholder_env_variable_is_rejected(monkeypatch):
    monkeypatch.setenv("NEWS_API_KEY", "PLEASE_FILL_YOUR_NEWS_API_KEY")
    with pytest.raises(ValueError):
        ai_reporter.require_env("NEWS_API_KEY")


# ---------- Data fetching ----------


@patch("ai_reporter.requests.get")
def test_get_weather_for_city(mock_get):
    mock_get.side_effect = [
        fake_response(GEOCODING_RESPONSE),
        fake_response(FORECAST_RESPONSE),
    ]

    result = ai_reporter.get_weather("Kampala")

    assert result["location"] == "Kampala, Uganda"
    assert result["temperature_2m"] == "26.3 °C"
    assert result["relative_humidity_2m"] == "59 %"
    assert result["wind_speed_10m"] == "2.7 km/h"
    assert "elevation" not in result  # only the needed fields are kept

    forecast_params = mock_get.call_args_list[1].kwargs["params"]
    assert forecast_params["latitude"] == 0.31
    assert forecast_params["longitude"] == 32.58
    assert all("timeout" in call.kwargs for call in mock_get.call_args_list)


@patch("ai_reporter.requests.get")
def test_get_weather_unknown_city(mock_get):
    mock_get.return_value = fake_response(
        {}
    )  # Open-Meteo omits "results" when nothing matches

    with pytest.raises(ValueError, match="not found"):
        ai_reporter.get_weather("Atlantisville")


@patch("ai_reporter.requests.get")
def test_get_news_keeps_only_needed_fields(mock_get, monkeypatch):
    monkeypatch.setenv("NEWS_API_KEY", "fake-news-key")
    mock_get.return_value = fake_response(
        {
            "status": "ok",
            "articles": [
                {
                    "title": "Test News Headline",
                    "description": "This is a test news description.",
                    "source": {"id": None, "name": "Test Source"},
                    "url": "https://example.com/story",
                    "urlToImage": "https://example.com/image.jpg",
                    "content": "Long article text...",
                }
            ],
        }
    )

    result = ai_reporter.get_news("ug")

    assert result == [
        {
            "title": "Test News Headline",
            "description": "This is a test news description.",
            "source": "Test Source",
        }
    ]
    assert mock_get.call_args.kwargs["params"]["country"] == "ug"


@patch("ai_reporter.requests.get")
def test_get_news_api_error(mock_get, monkeypatch):
    monkeypatch.setenv("NEWS_API_KEY", "fake-news-key")
    mock_get.return_value = fake_response(
        {"status": "error", "message": "apiKeyInvalid"}
    )

    with pytest.raises(ValueError, match="apiKeyInvalid"):
        ai_reporter.get_news("us")


# ---------- Prompts ----------


@pytest.mark.parametrize("report_type", list(ai_reporter.REPORT_TYPES))
def test_every_report_type_has_a_prompt(report_type):
    messages = ai_prompt.build_messages(report_type, {"key": "value"}, "Kampala")

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert '"key": "value"' in messages[1]["content"]
    assert "Kampala" in messages[1]["content"]
    assert "{data}" not in messages[1]["content"]


def test_missing_prompt_template_raises():
    with pytest.raises(ValueError, match="not found"):
        ai_prompt.load_prompt("does_not_exist")


# ---------- AI report generation ----------


@patch("ai_reporter.OpenAI")
def test_generate_report(mock_openai, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-openrouter-key")
    client = mock_openai.return_value
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="  Sunny report  "))]
    )

    report = ai_reporter.generate_report(
        "weather", {"temperature_2m": "26 °C"}, "Kampala"
    )

    assert report == "Sunny report"
    call = client.chat.completions.create.call_args.kwargs
    assert call["model"] == ai_reporter.CONFIG["ai"]["model"]
    assert [m["role"] for m in call["messages"]] == ["system", "user"]


@patch("ai_reporter.OpenAI")
def test_generate_report_empty_response(mock_openai, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-openrouter-key")
    mock_openai.return_value.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
    )

    with pytest.raises(ValueError, match="empty"):
        ai_reporter.generate_report("weather", {}, "Kampala")


class FakeStatusError(APIError):
    """An APIError with a status code, built without real HTTP objects."""

    def __init__(self, status_code):
        Exception.__init__(self, f"HTTP {status_code}")
        self.status_code = status_code


@pytest.mark.parametrize(
    "status_code, expected",
    [
        (401, "OPENROUTER_API_KEY"),
        (402, "credits"),
        (429, "Rate limit"),
        (503, "overloaded"),
    ],
)
def test_describe_api_error_status_codes(status_code, expected):
    assert expected in ai_reporter.describe_api_error(FakeStatusError(status_code))


def test_describe_api_error_timeout():
    error = APITimeoutError.__new__(APITimeoutError)
    assert "too long" in ai_reporter.describe_api_error(error)


def test_describe_api_error_unknown_code():
    assert "418" in ai_reporter.describe_api_error(FakeStatusError(418))


# ---------- Email ----------


@patch("ai_reporter.smtplib.SMTP_SSL")
def test_send_email(mock_smtp, monkeypatch):
    monkeypatch.setenv("GMAIL_ADDRESS", "sender@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "fake-app-password")
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    ai_reporter.send_email(
        "recipient@gmail.com", "Test Subject", "This is a test email."
    )

    mock_smtp.assert_called_once_with("smtp.gmail.com", 465)
    mock_server.login.assert_called_once_with("sender@gmail.com", "fake-app-password")
    sent = mock_server.send_message.call_args.args[0]
    assert sent["To"] == "recipient@gmail.com"
    assert sent["Subject"] == "Test Subject"


# ---------- Full program ----------


@patch("ai_reporter.send_email")
@patch("ai_reporter.generate_report", return_value="AI weather report")
@patch("ai_reporter.get_weather", return_value={"location": "Gulu, Uganda"})
def test_main_weather_success(mock_weather, mock_report, mock_send):
    exit_code = ai_reporter.main(["test@gmail.com", "weather", "--city", "Gulu"])

    assert exit_code == 0
    mock_weather.assert_called_once_with("Gulu")
    mock_send.assert_called_once_with(
        "test@gmail.com", "AI Weather Report: Gulu, Uganda", "AI weather report"
    )


@patch("ai_reporter.send_email")
def test_main_invalid_email_returns_error(mock_send):
    assert ai_reporter.main(["not-an-email", "weather"]) == 1
    mock_send.assert_not_called()


@patch("ai_reporter.send_email")
def test_main_invalid_report_type_returns_error(mock_send):
    assert ai_reporter.main(["test@gmail.com", "sports"]) == 1
    mock_send.assert_not_called()


@patch("ai_reporter.get_weather", side_effect=ValueError("City 'X' was not found."))
def test_main_handles_errors(mock_weather, capsys):
    assert ai_reporter.main(["test@gmail.com", "weather", "--city", "X"]) == 1
    assert "not found" in capsys.readouterr().out


def test_env_example_lists_every_required_key():
    env_example = (Path(__file__).parent / ".env.example").read_text(encoding="utf-8")
    for key in [
        "OPENROUTER_API_KEY",
        "NEWS_API_KEY",
        "GMAIL_ADDRESS",
        "GMAIL_APP_PASSWORD",
    ]:
        assert f"{key}=" in env_example
