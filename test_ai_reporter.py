import ai_reporter
from unittest.mock import patch, MagicMock


def test_validate_email_valid():
    assert ai_reporter.validate_email("test@gmail.com") is True


def test_validate_email_invalid():
    assert ai_reporter.validate_email("testgmail.com") is False


def test_validate_report_type_valid():
    assert ai_reporter.validate_report_type("weather") is True
    assert ai_reporter.validate_report_type("news_summary") is True


def test_validate_report_type_invalid():
    assert ai_reporter.validate_report_type("sports") is False


@patch("ai_reporter.requests.get")
def test_get_weather(mock_get):
    mock_response = MagicMock()

    mock_response.json.return_value = {
        "current": {
            "temperature_2m": 26.3,
            "relative_humidity_2m": 59,
            "wind_speed_10m": 2.7
        }
    }

    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = ai_reporter.get_weather()

    assert result["current"]["temperature_2m"] == 26.3
    assert result["current"]["relative_humidity_2m"] == 59
    assert result["current"]["wind_speed_10m"] == 2.7

    mock_get.assert_called_once()


@patch("ai_reporter.requests.get")
def test_get_news(mock_get):
    mock_response = MagicMock()

    mock_response.json.return_value = {
        "status": "ok",
        "articles": [
            {
                "title": "Test News Headline",
                "description": "This is a test news description."
            }
        ]
    }

    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch.dict(
        "os.environ",
        {"NEWS_API_KEY": "fake-news-key"}
    ):
        result = ai_reporter.get_news()

    assert len(result) == 1
    assert result[0]["title"] == "Test News Headline"
    assert result[0]["description"] == "This is a test news description."

    mock_get.assert_called_once()


@patch("ai_reporter.smtplib.SMTP_SSL")
def test_send_email(mock_smtp):
    mock_server = MagicMock()

    mock_smtp.return_value.__enter__.return_value = mock_server

    with patch.dict(
        "os.environ",
        {
            "GMAIL_ADDRESS": "sender@gmail.com",
            "GMAIL_APP_PASSWORD": "fake-app-password"
        }
    ):
        ai_reporter.send_email(
            "recipient@gmail.com",
            "Test Subject",
            "This is a test email."
        )

    mock_smtp.assert_called_once_with(
        "smtp.gmail.com",
        465
    )

    mock_server.login.assert_called_once_with(
        "sender@gmail.com",
        "fake-app-password"
    )

    mock_server.send_message.assert_called_once()