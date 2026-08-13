# AI Reporter

## Overview

AI Reporter is a Python command-line application that collects real-time weather or news data, uses an AI model to generate a short human-readable report, and sends the report to an email address.

The application supports two report types:

- `weather` — Generates a weather report using Open-Meteo.
- `news_summary` — Generates a news summary using NewsAPI.

The project demonstrates API integration, AI processing, email automation, environment variables, error handling, and unit testing.

---

## Technologies Used

- **Python** — Main programming language
- **Requests** — Communicates with external APIs
- **Open-Meteo API** — Provides weather data
- **NewsAPI** — Provides news data
- **OpenRouter** — Generates AI-powered reports
- **OpenAI Python Library** — Connects the application to OpenRouter
- **Gmail SMTP** — Sends reports by email
- **Pytest** — Runs automated tests
- **unittest.mock** — Mocks external services during testing
- **python-dotenv** — Loads environment variables from `.env`
**Black** Python code formatter used to maintain consistent PEP 8-style formatting
---

## Project Structure

```text
AI reporter/
│
├── ai_reporter.py
├── test_ai_reporter.py
├── requirements.txt
├── README.md
├── .env
└── .gitignore
```

### File Descriptions

- `ai_reporter.py` — Contains the main application logic.
- `test_ai_reporter.py` — Contains the unit tests.
- `requirements.txt` — Contains the project dependencies.
- `.env` — Stores private API keys and email credentials.
- `.gitignore` — Prevents sensitive and unnecessary files from being tracked.
- `README.md` — Contains project documentation.

---

## Setup

### 1. Create the project environment

Create and enter the project directory:

```bash
mkdir ai_reporter_project
cd ai_reporter_project
```

Create a virtual environment to keep the project's dependencies isolated:

```bash
python -m venv venv
```

Activate the virtual environment in Git Bash on Windows:

```bash
source venv/Scripts/activate
```

The terminal should show `(venv)` when the environment is active.

### 2. Install dependencies

Install the required Python packages:

```bash
pip install openai requests pytest python-dotenv
```

The installed dependencies can then be saved to `requirements.txt`:

```bash
pip freeze > requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project directory and add the required credentials:

```text
OPENROUTER_API_KEY=your_openrouter_api_key
NEWS_API_KEY=your_news_api_key
GMAIL_ADDRESS=your_gmail_address
GMAIL_APP_PASSWORD=your_gmail_app_password
```

The application uses `python-dotenv` to load these values without placing credentials directly in the Python code.

The `.env` file is excluded from Git using `.gitignore`.

### 4. Run the application

The application requires an email address and a report type.

For a weather report:

```bash
python ai_reporter.py test@gmail.com weather
```

For a news summary:

```bash
python ai_reporter.py test@gmail.com news_summary
```

The application retrieves the requested information, sends it to OpenRouter for processing, and sends the generated report to the specified email address.

---

## How It Works

```text
Command-line Input
        |
        v
Input Validation
        |
        v
Weather API / NewsAPI
        |
        v
OpenRouter AI
        |
        v
Generate Report
        |
        v
Gmail SMTP
        |
        v
Email Recipient
```

### Weather Report

The application uses Open-Meteo to retrieve:

- Temperature
- Relative humidity
- Wind speed

The weather data is then sent to OpenRouter, which generates a short and readable weather report.

### News Summary

The application uses NewsAPI to retrieve news headlines and descriptions.

The collected information is sent to OpenRouter, which generates a concise news summary without adding information that was not provided by the API.

---

## Error Handling

The application validates the email address and report type before processing the request.

It also handles errors from:

- Weather and news APIs
- Missing API keys
- OpenRouter
- Gmail SMTP

This prevents unexpected failures and provides useful error messages to the user.

---

## Testing

The project uses **Pytest** and **unittest.mock** for unit testing.

External services are mocked during testing so that the tests do not make real API requests or send real emails.

The tests cover:

- Valid email validation
- Invalid email validation
- Valid report types
- Invalid report types
- Weather API response handling
- NewsAPI response handling
- Email functionality

Run the tests with:

```bash
pytest -v
```

Current test result:

```text
7 passed
```

---

## Security

Sensitive credentials are stored in `.env` instead of being written directly into the source code.

The `.gitignore` file excludes sensitive and unnecessary files:

```text
.env
venv/
__pycache__/
.pytest_cache/
*.pyc
```

Real API keys and Gmail credentials should never be committed to a public repository.

---

## Future Improvements

- Allow users to select different cities for weather reports.
- Allow users to select different countries for news reports.
- Add additional report types.
- Add scheduled reports.
- Support HTML-formatted emails.

---

## Conclusion

AI Reporter demonstrates how Python can combine external APIs, AI, email automation, environment-based configuration, error handling, and automated testing into a single practical application.