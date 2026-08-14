import sys
import requests
import os
import smtplib

from email.mime.text import MIMEText
from openai import OpenAI, APIError, AuthenticationError
from dotenv import load_dotenv

from ai_prompt import report_prompt


load_dotenv()


def validate_email(email):
    """Check if the email looks valid."""
    return "@" in email and "." in email


def validate_report_type(report_type):
    """Check if the report type is supported."""
    return report_type in ["weather", "news_summary"]


def get_weather():
    """Get current weather information."""

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": 0.3,
        "longitude": 32.6,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "timezone": "Africa/Kampala",
    }

    response = requests.get(url, params=params)

    response.raise_for_status()

    return response.json()


def get_news():
    """Get top news headlines from NewsAPI."""

    api_key = os.getenv("NEWS_API_KEY")

    if not api_key:
        raise ValueError("NEWS_API_KEY is not set.")

    url = "https://newsapi.org/v2/top-headlines"

    params = {
        "country": "us",
        "apiKey": api_key,
        "pageSize": 5,
    }

    response = requests.get(url, params=params, timeout=10)

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "ok":
        raise ValueError(
            data.get("message", "News API returned an error.")
        )

    return data["articles"]


def generate_report(report_type, data):
    """Use OpenRouter AI to create a human-readable report."""

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set.")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    prompt = report_prompt(report_type, data)

    response = client.chat.completions.create(
        model="openai/gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=500,
    )

    return response.choices[0].message.content


def send_email(recipient, subject, body):
    """Send the report to the recipient using Gmail."""

    sender = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender:
        raise ValueError("GMAIL_ADDRESS is not set.")

    if not app_password:
        raise ValueError("GMAIL_APP_PASSWORD is not set.")

    message = MIMEText(body)

    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.send_message(message)


def main():
    """Run the program."""

    if len(sys.argv) != 3:
        print("Usage: python ai_reporter.py <email> <report_type>")
        return

    email = sys.argv[1]
    report_type = sys.argv[2]

    if not validate_email(email):
        print("Invalid email.")
        return

    if not validate_report_type(report_type):
        print("Invalid report type.")
        return

    try:
        if report_type == "weather":
            weather = get_weather()

            report = generate_report("weather", weather)

            print(report)

            send_email(email, "AI Weather Report", report)

            print("Weather report sent successfully.")

        elif report_type == "news_summary":
            news = get_news()

            report = generate_report("news_summary", news)

            print(report)

            send_email(email, "AI News Summary", report)

            print("News report sent successfully.")

    except AuthenticationError:
        print("OpenRouter authentication failed.")
        print("Please check your OPENROUTER_API_KEY.")

    except APIError as error:
        print("OpenRouter could not generate the report.")
        print(f"Error: {error}")

    except requests.exceptions.RequestException as error:
        print(f"Could not get {report_type} information.")
        print(f"Error: {error}")

    except ValueError as error:
        print(f"Error: {error}")

    except smtplib.SMTPException as error:
        print("Could not send the email.")
        print(f"Error: {error}")


if __name__ == "__main__":
    main()