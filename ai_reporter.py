"""
AI Reporter

Fetches weather or news data from a public API, turns it into a short
human-readable report with an AI model (via OpenRouter), and emails it.

Usage:
    python ai_reporter.py <email> weather [--city CITY]
    python ai_reporter.py <email> news_summary [--country CODE]
"""

import argparse
import json
import os
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

import requests
from dotenv import load_dotenv
from email_validator import EmailNotValidError, validate_email as check_email
from openai import APIConnectionError, APIError, APITimeoutError, OpenAI

from ai_prompt import build_messages

load_dotenv()

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config(path=CONFIG_PATH):
    """Load settings (API URLs, model name, defaults) from config.json."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


CONFIG = load_config()

# Friendly messages for the HTTP status codes returned by the OpenAI-compatible API.
# Based on https://developers.openai.com/api/docs/guides/error-codes
# plus OpenRouter-specific codes (402, 408, 502).
API_ERROR_MESSAGES = {
    400: "The request to the AI service was invalid. Check the model name in config.json.",
    401: "Authentication failed. Check OPENROUTER_API_KEY in your .env file.",
    402: "Your OpenRouter account has run out of credits. Add credits and try again.",
    403: "Access was denied. Your key may not have access to this model or region.",
    404: "The AI model was not found. Check the model name in config.json.",
    408: "The AI service timed out. Please try again.",
    429: "Rate limit or quota reached. Wait a moment and try again.",
    500: "The AI service had an internal error. Please try again later.",
    502: "The AI model is temporarily unavailable. Please try again later.",
    503: "The AI service is overloaded. Please try again later.",
}


# ---------- Input validation ----------


def validate_email(email):
    """Check the email address format using the email-validator package."""
    try:
        check_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def validate_report_type(report_type):
    """Check if the report type is supported."""
    return report_type in REPORT_TYPES


def require_env(name):
    """Return an environment variable, or raise a clear error if it is missing."""
    value = os.getenv(name)
    if not value or value.startswith("PLEASE_FILL"):
        raise ValueError(
            f"{name} is not set. Copy .env.example to .env and fill it in."
        )
    return value


# ---------- Data fetching ----------


def find_city(city):
    """Look up a city's coordinates with the Open-Meteo geocoding API."""
    response = requests.get(
        CONFIG["weather"]["geocoding_url"],
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=CONFIG["request_timeout_seconds"],
    )
    response.raise_for_status()
    results = response.json().get("results")
    if not results:
        raise ValueError(f"City '{city}' was not found.")

    place = results[0]
    name = ", ".join(part for part in [place.get("name"), place.get("country")] if part)
    return place["latitude"], place["longitude"], name


def get_weather(city):
    """Get current weather for a city, keeping only the fields the AI needs."""
    latitude, longitude, location = find_city(city)
    fields = CONFIG["weather"]["current_fields"]

    response = requests.get(
        CONFIG["weather"]["forecast_url"],
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join(fields),
            "timezone": "auto",
        },
        timeout=CONFIG["request_timeout_seconds"],
    )
    response.raise_for_status()
    data = response.json()

    current = data.get("current", {})
    units = data.get("current_units", {})
    weather = {"location": location, "time": current.get("time")}
    for field in fields:
        if field in current:
            weather[field] = f"{current[field]} {units.get(field, '')}".strip()
    return weather


def get_news(country):
    """Get top headlines from NewsAPI, keeping only the fields the AI needs."""
    api_key = require_env("NEWS_API_KEY")

    response = requests.get(
        CONFIG["news"]["url"],
        params={
            "country": country,
            "pageSize": CONFIG["news"]["page_size"],
            "apiKey": api_key,
        },
        timeout=CONFIG["request_timeout_seconds"],
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "ok":
        raise ValueError(data.get("message", "NewsAPI returned an error."))

    articles = [
        {
            "title": article.get("title"),
            "description": article.get("description"),
            "source": (article.get("source") or {}).get("name"),
        }
        for article in data.get("articles", [])
    ]
    if not articles:
        raise ValueError(f"No news headlines were found for country '{country}'.")
    return articles


# ---------- AI report generation ----------


def generate_report(report_type, data, location):
    """Use the AI model (via OpenRouter) to turn the data into a readable report."""
    ai = CONFIG["ai"]
    client = OpenAI(
        base_url=ai["base_url"],
        api_key=require_env("OPENROUTER_API_KEY"),
        timeout=ai["timeout_seconds"],
        max_retries=ai["max_retries"],  # retries 429 and 5xx errors automatically
    )

    response = client.chat.completions.create(
        model=ai["model"],
        messages=build_messages(report_type, data, location),
        temperature=ai["temperature"],
        max_tokens=ai["max_tokens"],
    )

    report = response.choices[0].message.content
    if not report or not report.strip():
        raise ValueError("The AI returned an empty report.")
    return report.strip()


def describe_api_error(error):
    """Turn an OpenAI/OpenRouter error into a friendly message."""
    if isinstance(error, APITimeoutError):
        return "The AI service took too long to respond. Please try again."
    if isinstance(error, APIConnectionError):
        return "Could not connect to the AI service. Check your internet connection."
    status = getattr(error, "status_code", None)
    return API_ERROR_MESSAGES.get(
        status, f"The AI service returned an error ({status})."
    )


# ---------- Email ----------


def send_email(recipient, subject, body):
    """Send the report to the recipient using Gmail."""
    sender = require_env("GMAIL_ADDRESS")
    app_password = require_env("GMAIL_APP_PASSWORD")

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient

    settings = CONFIG["email"]
    with smtplib.SMTP_SSL(settings["smtp_host"], settings["smtp_port"]) as server:
        server.login(sender, app_password)
        server.send_message(message)


# ---------- Report types ----------
# To add a new report type: add an entry here and a matching prompts/<type>.txt file.

REPORT_TYPES = {
    "weather": {
        "fetch": lambda options: get_weather(options.city),
        "location": lambda options, data: data["location"],
        "subject": "AI Weather Report: {location}",
    },
    "news_summary": {
        "fetch": lambda options: get_news(options.country),
        "location": lambda options, data: options.country.upper(),
        "subject": "AI News Summary: {location}",
    },
}


# ---------- Command line ----------


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Generate an AI weather or news report and email it."
    )
    parser.add_argument("email", help="email address to send the report to")
    parser.add_argument("report_type", help=f"one of: {', '.join(REPORT_TYPES)}")
    parser.add_argument(
        "--city",
        default=CONFIG["weather"]["default_city"],
        help="city for weather reports (default: %(default)s)",
    )
    parser.add_argument(
        "--country",
        default=CONFIG["news"]["default_country"],
        help="2-letter country code for news reports (default: %(default)s)",
    )
    return parser.parse_args(argv)


def run(options):
    """Fetch data, generate the report and email it. Returns an exit code."""
    report = REPORT_TYPES[options.report_type]

    try:
        data = report["fetch"](options)
        location = report["location"](options, data)
        text = generate_report(options.report_type, data, location)
        print(text)
        send_email(options.email, report["subject"].format(location=location), text)
        print(f"\nReport sent successfully to {options.email}.")
        return 0

    except APIError as error:
        print(f"AI error: {describe_api_error(error)}")
    except requests.exceptions.RequestException as error:
        print(f"Could not get {options.report_type} data: {error}")
    except smtplib.SMTPAuthenticationError:
        print("Gmail login failed. Check GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env.")
    except smtplib.SMTPException as error:
        print(f"Could not send the email: {error}")
    except OSError as error:
        print(f"Network error while sending the email: {error}")
    except ValueError as error:
        print(f"Error: {error}")
    return 1


def main(argv=None):
    options = parse_args(sys.argv[1:] if argv is None else argv)

    if not validate_email(options.email):
        print(f"Invalid email address: {options.email}")
        return 1

    if not validate_report_type(options.report_type):
        print(f"Invalid report type. Choose one of: {', '.join(REPORT_TYPES)}")
        return 1

    return run(options)


if __name__ == "__main__":
    sys.exit(main())
