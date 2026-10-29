# AI Reporter

## Overview

AI Reporter is a Python command-line application that collects real-time weather or news data, uses an AI model to turn it into a short human-readable report, and emails the report to a chosen address.

It supports two report types:

- `weather`: current weather for **any city**, using the Open-Meteo geocoding and forecast APIs
- `news_summary`: top headlines for **any supported country**, using NewsAPI

The project demonstrates API integration, prompt engineering, AI processing, email automation, external configuration, error handling and unit testing.

---

## Technologies Used

- **Python**: main programming language
- **Requests**: calls the external APIs
- **Open-Meteo API**: geocoding (city → coordinates) and current weather; no key needed
- **NewsAPI**: news headlines
- **OpenRouter**: generates the AI reports
- **OpenAI Python library**: connects to OpenRouter's OpenAI-compatible API
- **Gmail SMTP (`smtplib`)**: sends the reports by email
- **email-validator**: robust email address validation
- **python-dotenv**: loads credentials from `.env`
- **argparse**: command-line arguments and options
- **Pytest** and **unittest.mock**: automated tests with mocked external services
- **Black**: code formatting (PEP 8 style)

---

## Project Structure

```text
ai-reporter/
├── ai_reporter.py         # Main application logic
├── ai_prompt.py           # Loads prompt templates and builds the AI messages
├── config.json            # API URLs, model name, defaults and other settings
├── prompts/
│   ├── system.txt         # Shared instructions for the AI (identity and rules)
│   ├── weather.txt        # Weather report template, with an example
│   └── news_summary.txt   # News summary template, with an example
├── test_ai_reporter.py    # Unit tests
├── requirements.txt       # Dependencies
├── .env.example           # Template for credentials (safe to commit)
├── .env                   # Your real credentials (never committed)
├── .gitignore
└── README.md
```

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/Scripts/activate      # Git Bash on Windows
# venv\Scripts\activate           # Command Prompt
# source venv/bin/activate        # macOS / Linux
```

The terminal shows `(venv)` when the environment is active.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure credentials

Copy the template and fill in your own values:

```bash
cp .env.example .env
```

```text
OPENROUTER_API_KEY=PLEASE_FILL_YOUR_OPENROUTER_API_KEY
NEWS_API_KEY=PLEASE_FILL_YOUR_NEWS_API_KEY
GMAIL_ADDRESS=PLEASE_FILL_YOUR_GMAIL_ADDRESS
GMAIL_APP_PASSWORD=PLEASE_FILL_YOUR_GMAIL_APP_PASSWORD
```

`.env.example` is committed so others know which values are needed. `.env` is listed in `.gitignore` and is never committed. If a value is missing or still a placeholder, the program stops with a clear message saying which one.

### 4. (Optional) Adjust settings

Settings live in `config.json` rather than in the code, so they can be changed without editing Python:

| Setting | Purpose |
|---|---|
| `ai.model`, `ai.temperature`, `ai.max_tokens` | Which model to use and how it responds |
| `ai.timeout_seconds`, `ai.max_retries` | How long to wait for the AI and how often to retry |
| `weather.default_city`, `weather.current_fields` | Default city and which weather values to fetch |
| `news.default_country`, `news.page_size` | Default country and number of headlines |
| `*_url`, `email.smtp_host`, `email.smtp_port` | API endpoints and mail server |

---

## Usage

```bash
python ai_reporter.py <email> <report_type> [--city CITY] [--country CODE]
```

| Example | What it does |
|---|---|
| `python ai_reporter.py me@gmail.com weather` | Weather for the default city (Kampala) |
| `python ai_reporter.py me@gmail.com weather --city Nairobi` | Weather for Nairobi |
| `python ai_reporter.py me@gmail.com news_summary` | Top headlines for the default country (US) |
| `python ai_reporter.py me@gmail.com news_summary --country gb` | Top headlines for the UK |
| `python ai_reporter.py --help` | Show all options |

NewsAPI's free plan only supports some countries for top headlines. If a country returns no stories, the program says so.

The program exits with code `0` on success and `1` on any error, so it can be used safely in scripts and scheduled jobs.

---

## How It Works

```text
Command-line arguments (email, report type, --city / --country)
        │
        ▼
Input validation (email-validator, supported report types)
        │
        ▼
Fetch data ── weather: city → coordinates → current weather (Open-Meteo)
           └─ news:    top headlines for the country (NewsAPI)
        │
        ▼
Keep only the fields the AI needs
        │
        ▼
Build prompt from prompts/*.txt  →  OpenRouter AI  →  report text
        │
        ▼
Gmail SMTP  →  recipient
```

### Keeping the AI input small

Before calling the AI, the program removes everything the report doesn't need. For news, only `title`, `description` and `source` are kept (no URLs, image links or full article text). For weather, each value is combined with its unit (`26.3 °C`). This lowers token cost and gives the model less noise to get confused by.

### Adding a new report type

1. Add an entry to `REPORT_TYPES` in `ai_reporter.py` with a fetch function and an email subject.
2. Add a matching `prompts/<report_type>.txt` template.

A test checks that every report type has a prompt template.

---

## Prompt Design

Prompts are stored as text files in `prompts/` instead of inside the Python code, so they can be improved without touching the program logic. They follow [OpenAI's prompt engineering guidelines](https://developers.openai.com/api/docs/guides/prompt-engineering):

- **A system message** (`system.txt`) sets the identity and the rules that apply to every report: use only the provided data, never invent facts, plain text suitable for email, under 150 words.
- **A user message** (`weather.txt` / `news_summary.txt`) describes the task, gives **one example** of input data and the expected report (few-shot prompting), and wraps the real data in `<data>` tags so the model can clearly tell instructions from data.
- `{placeholders}` such as `{data}` and `{location}` are filled in with Python's `str.format`. Literal braces in a template are written as `{{ }}`.

---

## Error Handling

The program validates its input first, then handles failures at each step with a clear message and exit code `1`:

| Failure | Message |
|---|---|
| Invalid email or report type | Says what was wrong and lists the valid report types |
| Missing or placeholder credential in `.env` | Names the missing variable |
| City not found | `City '<name>' was not found.` |
| Weather / news API failure or timeout | `Could not get <report type> data: ...` |
| NewsAPI error (e.g. invalid key) | Shows NewsAPI's own message |
| AI service errors | Friendly message per status code (see below) |
| Empty AI response | `The AI returned an empty report.` |
| Gmail login failure | Asks you to check `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` |
| Other email or network failures | `Could not send the email: ...` |

### AI error codes

Based on [OpenAI's error codes](https://developers.openai.com/api/docs/guides/error-codes) plus OpenRouter-specific codes:

| Code | Meaning |
|---|---|
| 400 / 404 | Invalid request or unknown model; check `config.json` |
| 401 | Invalid API key |
| 402 | OpenRouter credits exhausted |
| 403 | No access to this model or region |
| 408 / timeout | The AI took too long to respond |
| 429 | Rate limit or quota reached |
| 500 / 502 / 503 | Server error, model unavailable or overloaded |
| Connection error | No internet or the service is unreachable |

The OpenAI client also **automatically retries** rate-limit (429) and server (5xx) errors with backoff, up to `ai.max_retries` times, before an error is shown.

---

## Testing

The tests use **Pytest** and **unittest.mock**. External services (Open-Meteo, NewsAPI, OpenRouter, Gmail) are mocked, so the tests make no real API calls and send no real emails.

They cover:

- Valid and invalid email addresses, and supported and unsupported report types
- Missing and placeholder credentials
- City lookup, unknown cities, and trimming the weather data
- Trimming news articles to the needed fields, and NewsAPI errors
- A prompt template for every report type, and missing templates
- AI report generation, empty AI responses, and messages for AI error codes
- Email construction and sending
- The full program flow, including exit codes for success and failure
- `.env.example` listing every required key

```bash
pytest -v
```

Current result: **30 passed**

---

## Security

- Credentials are stored in `.env`, never in the code.
- `.env.example` shows the required keys with placeholders only.
- `.gitignore` excludes:

```text
.env
venv/
__pycache__/
.pytest_cache/
*.pyc
```

Real API keys and Gmail credentials should never be committed to a public repository.

---

## Changes After Review

| Reviewer feedback | Change made |
|---|---|
| Provide a `.env.example` with placeholders | Added `.env.example`; placeholders are detected and rejected with a clear message |
| Make location and URLs flexible | `--city` and `--country` options; city lookup through the Open-Meteo geocoding API; URLs moved to `config.json` |
| Handle API error codes | Friendly messages per status code, connection and timeout handling, automatic retries |
| Use a package for email validation | Replaced the manual check with `email-validator` |
| Separate prompts and configuration from code | Prompts in `prompts/*.txt` with `{placeholders}`; settings (URLs, model, defaults) in `config.json` |
| Follow prompt engineering guidelines and add examples | System message plus task prompts with a worked example each, and data wrapped in `<data>` tags |

Other improvements:
- Timeouts on every API request
- Only the needed fields are sent to the AI
- Report types defined in one place
- Non-zero exit codes on failure
- More tests (from 7 to 30)

---

## Future Improvements

- Add more report types (e.g. currency rates, stock updates)
- Send HTML-formatted emails
- Schedule daily reports
- Use Jinja2 templates for more advanced prompt logic

---

## Conclusion

AI Reporter shows how Python can combine public APIs, an AI model, email automation, external configuration, careful error handling and automated testing into one practical application.
