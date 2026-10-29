"""Load prompt templates from the prompts/ folder and build chat messages."""

import json
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name, **values):
    """
    Read prompts/<name>.txt and fill in its {placeholders}.

    Literal braces inside a template must be doubled ({{ and }}).
    """
    path = PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise ValueError(f"Prompt template not found: {path.name}")
    template = path.read_text(encoding="utf-8")
    return template.format(**values)


def build_messages(report_type, data, location):
    """Build the system and user messages sent to the AI model."""
    data_text = json.dumps(data, indent=2, ensure_ascii=False)
    return [
        {"role": "system", "content": load_prompt("system")},
        {
            "role": "user",
            "content": load_prompt(report_type, data=data_text, location=location),
        },
    ]
