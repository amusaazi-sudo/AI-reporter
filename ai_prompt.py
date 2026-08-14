def report_prompt(report_type, data):
    """Create the appropriate AI prompt for the selected report type."""

    if report_type == "weather":
        return f"""
Create a short and friendly weather report.

Include:
- Temperature
- Humidity
- Wind speed
- A simple practical suggestion

Use only the information provided.

Weather data:
{data}
"""

    elif report_type == "news_summary":
        return f"""
Create a short and easy-to-read news summary.

For each important story:
- Give the headline
- Give a short 1-2 sentence summary

Do not invent information.

News data:
{data}
"""

    raise ValueError("Unsupported report type.")