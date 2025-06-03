# contact_reminder.py
import os
import random
from datetime import datetime
from pathlib import Path
import subprocess
from contacts.contact import Contact
from contacts.ingest import load_contacts
from contacts.print import format_timedelta


# Chance of contacting a contact randomly
CONTACT_FRACTION = 0.01


def check_contacts(contacts: list[Contact]) -> tuple[list[str], list[str]]:
    now = datetime.now()
    overdue = []
    suggestions = []

    for contact in contacts:
        last_contact = contact.get_latest_contact_date()
        if not last_contact or not contact.get_frequency_timedelta():
            continue

        time_since = now - last_contact
        if time_since > contact.get_frequency_timedelta():
            days = time_since.days
            overdue.append(
                f"{contact.name} ({format_timedelta(time_since)} > {contact.frequency})"
            )
        elif random.random() < CONTACT_FRACTION:
            days = time_since.days
            suggestions.append(f"{contact.name} ({format_timedelta(time_since)})")

    return overdue, suggestions


def show_notification(overdue: list[str], suggestions: list[str]):
    message = "You are overdue:\n"
    message += "\n".join(f"\t{item}" for item in overdue)

    if suggestions:
        message += "\n\nHow about getting in contact?\n"
        message += "\n".join(f"\t{item}" for item in suggestions)

    subprocess.run(
        ["zenity", "--info", "--title", "Contact Reminders", "--text", message]
    )


def main():
    # Get YAML path from environment variable
    yaml_path = os.environ.get("CONTACTS")
    if not yaml_path:
        raise FileNotFoundError("Error: CONTACTS environment variable not set")
    yaml_path = Path(yaml_path)

    contacts = load_contacts(yaml_path)
    overdue, suggestions = check_contacts(contacts)
    if overdue or suggestions:
        show_notification(overdue, suggestions)


if __name__ == "__main__":
    main()
