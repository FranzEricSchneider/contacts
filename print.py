#!/usr/bin/env python3
"""Script to display contact information in various formats."""

import argparse
import os
from pathlib import Path
from typing import Dict, List, Set
import yaml
from datetime import datetime
from collections import defaultdict
from Levenshtein import distance
from colorama import Fore, Style, init

from contact import Contact
from ingest import load_contacts


def get_last_name(name: str) -> str:
    """Extract last name from a full name for sorting."""
    return name.split()[-1]


def has_issues(text: str, name: bool = False) -> bool:
    """Check if text contains any issue markers."""
    if name:
        return any(marker in text for marker in ["?", "TODO"])
    else:
        return "TODO" in text


def get_field_color(contact: Contact, field_name: str) -> str:
    """Determine the color for a field based on its content and issues."""

    field_value = getattr(contact, field_name, [])
    
    # Check for issues in the field
    if field_name == "name":
        if has_issues(contact.name, name=True):
            return Fore.MAGENTA
    elif isinstance(field_value, list):
        if any(has_issues(str(item)) for item in field_value):
            return Fore.MAGENTA
    elif field_value and has_issues(str(field_value)):
        return Fore.MAGENTA

    # Check if field is empty
    if not field_value:
        if field_name in ("address", "update"):
            return Fore.RED
        elif field_name == "frequency":
            return Fore.YELLOW
        else:
            return Fore.YELLOW
            
    # No issues, has content
    return Style.DIM


def format_field_name(contact: Contact, field_name: str) -> str:
    """Format field name with appropriate color and capitalization."""
    color = get_field_color(contact, field_name)
    name = field_name.upper() if color == Fore.MAGENTA else field_name
    return f"{color}{name}{Style.RESET_ALL}"


def print_missing(contacts: List[Contact]) -> None:
    """Print all names and their field statuses."""
    # Initialize colorama for cross-platform color support
    init()
    
    # Define fields to check in order
    fields = ["name", "address", "update", "frequency", "tag", "characteristic", "url"]
    
    # Print each contact name with padding
    for contact in sorted(contacts, key=lambda x: get_last_name(x.name)):
        print(f"{contact.name:<25}", end="")
        
        # Print status for each field
        for field in fields[1:]:  # Skip 'name' as it's already printed
            print(format_field_name(contact, field), end="    ")
        print()  # New line after each contact


def print_people(contacts: List[Contact]) -> None:
    """Print alphabetized list of contact names."""
    for name in sorted((contact.name for contact in contacts), key=get_last_name):
        print(name)


def print_places(contacts: List[Contact]) -> None:
    """Print locations and the people at each location."""
    # Create a mapping of locations to people
    location_map = defaultdict(list)
    
    for contact in contacts:
        # Get the most recent address
        if contact.address:
            latest_address = max(contact.address, key=lambda x: x[0])[1]
            location_map[latest_address].append(contact.name)
    
    # Print locations and their people
    for location in sorted(location_map.keys()):
        print(f"\n{location.upper()}")
        for name in sorted(location_map[location], key=get_last_name):
            print(f"\t{name}")


def find_best_match(partial_name: str, contacts: List[Contact]) -> Contact:
    """Find the contact that best matches the partial name."""
    if not contacts:
        raise ValueError("No contacts available")
        
    # Find the best match using Levenshtein distance
    return min(
        contacts,
        key=lambda c: min(
            distance(partial_name.lower(), part.lower())
            for part in c.name.split()
        )
    )


def print_person_summary(contact: Contact) -> None:
    """Print name, latest address, and all updates for a contact."""
    print(f"\nName: {contact.name}")
    
    # Print latest address
    if contact.address:
        latest_address = max(contact.address, key=lambda x: x[0])
        print(f"Address {latest_address[0].strftime('%Y-%m-%d')}: {latest_address[1]}")
    
    # Print all updates
    if contact.update:
        print("Updates:")
        for date, update in sorted(contact.update, key=lambda x: x[0]):
            print(f"\t{date.strftime('%Y-%m-%d')}: {update}")


def print_person_all(contact: Contact) -> None:
    """Print all information for a contact."""
    print(f"\nName: {contact.name}")
    
    if contact.address:
        print("\nAddresses:")
        for date, addr in sorted(contact.address, key=lambda x: x[0], reverse=True):
            print(f"\t{date.strftime('%Y-%m-%d')}: {addr}")
    
    if contact.frequency:
        print(f"\nFrequency: {contact.frequency}")
    
    if contact.update:
        print("\nUpdates:")
        for date, update in sorted(contact.update, key=lambda x: x[0]):
            print(f"\t{date.strftime('%Y-%m-%d')}: {update}")
    
    if contact.characteristic:
        print("\nCharacteristics:")
        for char in sorted(contact.characteristic):
            print(f"\t{char}")
    
    if contact.tag:
        print("\nTags:")
        for tag in sorted(contact.tag):
            print(f"\t{tag}")
    
    if contact.url:
        print("\nURLs:")
        for url in sorted(contact.url):
            print(f"\t{url}")


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Display contact information in various formats"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--people", action="store_true", help="Print alphabetized list of names")
    group.add_argument("--places", action="store_true", help="Print locations and people at each location")
    group.add_argument("--person", help="Print summary for person matching partial name")
    group.add_argument("--all", help="Print all information for person matching partial name")
    group.add_argument("--missing", action="store_true", help="Print all names with their field statuses")
    
    args = parser.parse_args()
    
    # Get YAML path from environment variable
    yaml_path = os.environ.get("CONTACTS")
    if not yaml_path:
        raise FileNotFoundError("Error: CONTACTS environment variable not set")
    yaml_path = Path(yaml_path)
    
    # Load contacts
    contacts = load_contacts(yaml_path)
    if not contacts:
        raise ValueError(f"No contacts found in {yaml_path}")
    
    # Process according to flags
    if args.people:
        print_people(contacts)
    elif args.places:
        print_places(contacts)
    elif args.person:
        contact = find_best_match(args.person, contacts)
        print_person_summary(contact)
    elif args.all:
        contact = find_best_match(args.all, contacts)
        print_person_all(contact)
    elif args.missing:
        print_missing(contacts)


if __name__ == "__main__":
    main() 