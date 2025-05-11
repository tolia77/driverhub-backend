import os
import requests
from app.settings import settings


def send_message(first_name, last_name, email, subject, text) -> requests.Response:
    return requests.post(
        "https://api.mailgun.net/v3/sandbox97853b721546409a962886efd01bcaf6.mailgun.org/messages",
        auth=("api", settings.mailgun.mailgun_api_key),
        data={"from": "Mailgun Sandbox <postmaster@sandbox97853b721546409a962886efd01bcaf6.mailgun.org>",
              "to": f"{first_name} {last_name} <{email}>",
              "subject": subject,
              "text": text})
