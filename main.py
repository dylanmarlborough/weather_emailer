import os
from pathlib import Path

# Load .env file for local development (not needed in GitHub Actions)
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

from weather import fetch_weather
from email_composer import compose_email
from mailer import send_email


def main():
    print("Fetching NYC weather...")
    hours = fetch_weather()

    print("Composing email...")
    subject, plain_text, html = compose_email(hours)

    print("Sending email...")
    send_email(subject, plain_text, html)

    print("Done.")


if __name__ == "__main__":
    main()
