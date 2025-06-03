#!/usr/bin/env python3
"""Script to ingest contact information from text files into a YAML database."""

import argparse
import os
from pathlib import Path
import sys
from typing import List, Dict, Tuple, NamedTuple
import yaml
from dataclasses import dataclass
from collections import defaultdict
from Levenshtein import distance

from contact import Contact


@dataclass
class ParsedData:
    """Container for parsed contact data with line numbers."""
    name: str
    data_pairs: List[Tuple[str, str]]
    name_line: int
    data_lines: Dict[Tuple[str, str], int]


def load_contacts(yaml_path: Path) -> List[Contact]:
    """Load contacts from a YAML file.
    Raises:
        FileNotFoundError: If the YAML file doesn't exist
    """

    if not yaml_path.exists():
        return []
        
    with yaml_path.open("r") as f:
        data = yaml.safe_load(f)
        return [Contact.from_dict(contact) for contact in data]


def save_contacts(contacts: List[Contact], yaml_path: Path) -> None:
    """Save contacts to a YAML file.
    Args:
        contacts: List of Contact objects to save
        yaml_path: Path to the YAML file
    """
    # Create parent directories if they don't exist
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    # Save contacts
    with yaml_path.open("w") as fout:
        yaml.safe_dump(
            [contact.to_dict() for contact in contacts],
            fout,
            sort_keys=True,
            indent=2,
        )


def parse_text_file(file_path: Path) -> List[ParsedData]:
    """Parse the input text file into a list of contacts and their data.
    
    Args:
        file_path: Path to the text file to parse
        
    Returns:
        List of ParsedData objects containing contact information and line numbers
    """
    contacts = []
    current_name = None
    current_data = []
    current_name_line = None
    current_data_lines = {}
    
    with file_path.open("r") as fin:
        for line_num, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a name line (no colon)
            if ":" not in line:
                # Save previous contact if it exists before starting a new name
                if current_name:
                    contacts.append(ParsedData(
                        name=current_name,
                        data_pairs=current_data,
                        name_line=current_name_line,
                        data_lines=current_data_lines
                    ))
                current_name = line
                current_name_line = line_num
                current_data = []
                current_data_lines = {}
            else:
                # Parse key-value pair
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                pair = (key, value)
                current_data.append(pair)
                current_data_lines[pair] = line_num
    
    # Add the last contact
    if current_name:
        contacts.append(ParsedData(
            name=current_name,
            data_pairs=current_data,
            name_line=current_name_line,
            data_lines=current_data_lines
        ))
    
    return contacts


def validate_contacts(parsed_data: List[ParsedData], text_file_path: Path) -> List[str]:
    """Validate all contact data before making any changes.
    
    Args:
        parsed_data: List of ParsedData objects to validate
        text_file_path: Path to the source file (for error messages)
        
    Returns:
        List of error messages, empty if validation passes
    """
    errors = []
    
    for contact_data in parsed_data:
        # Create a test contact to validate the data
        contact = Contact(name=contact_data.name)

        if len(contact_data.name.split(" ")) < 2:
            errors.append(
                f"Error in contact '{contact_data.name}' at line {contact_data.name_line} of {text_file_path}:\n"
                f"Looks like it's not a full name"
            )

        for key, value in contact_data.data_pairs:
            try:
                contact.update_data(key, value)
            except ValueError as e:
                line_num = contact_data.data_lines[(key, value)]
                errors.append(
                    f"Error in contact '{contact_data.name}' at line {line_num} of {text_file_path}:\n"
                    f"  {key}: {value}\n"
                    f"  {' ' * len(key)}  {'^' * len(value)}\n"
                    f"{str(e)}"
                )
    
    return errors


def validate_similar_names(new_names: List[str], existing_names: List[str], text_file_path: Path) -> List[str]:
    """Check for names that are very similar to existing names (possible typos).
    
    Args:
        new_names: List of names from the new data
        existing_names: List of names from existing contacts
        text_file_path: Path to the source file (for error messages)
        
    Returns:
        List of error messages for similar names
    """
    errors = []
    
    for new_name in new_names:
        for existing_name in existing_names:
            if new_name == existing_name:
                continue
                
            # Check Levenshtein distance
            dist = distance(new_name, existing_name)
            if 1 <= dist <= 2:
                errors.append(
                    f"Warning: Name '{new_name}' in {text_file_path} is similar to "
                    f"existing '{existing_name}' (+-{dist} character).\n"
                    f"If this is a typo, please correct it. If different, add functionality to ignore."
                )
    
    return errors


def update_contacts(yaml_path: Path, text_file_path: Path) -> None:
    """Update the YAML contacts database with information from a text file.
    
    Args:
        yaml_path: Path to the YAML database file
        text_file_path: Path to the text file with new contact information
        
    Raises:
        ValueError: If there are any validation errors in the input file
    """
    # Parse new data with line numbers
    new_data = parse_text_file(text_file_path)
    
    # Validate all data before making changes
    errors = validate_contacts(new_data, text_file_path)
    
    # Load existing contacts to check for similar names
    existing_contacts = load_contacts(yaml_path)
    errors.extend(
        validate_similar_names(
            [data.name for data in new_data],
            [contact.name for contact in existing_contacts],
            text_file_path
        )
    )
    
    if errors:
        error_msg = "\n\nFound {} error(s) in input file:\n{}".format(
            len(errors),
            "\n\n".join(errors)
        )
        raise ValueError(error_msg)
    
    # Load existing contacts
    contacts = {
        contact.name: contact
        for contact in existing_contacts
    }
    
    # Update contacts
    for parsed in new_data:
        if parsed.name not in contacts:
            # Create new contact
            contact = Contact(name=parsed.name)
            contacts[parsed.name] = contact
        
        # Update contact with new data
        for key, value in parsed.data_pairs:
            contacts[parsed.name].update_data(key, value)
    
    # Save updated contacts
    save_contacts(list(contacts.values()), yaml_path)


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Ingest contact information from a text file into a YAML database"
    )
    parser.add_argument(
        "text_file",
        type=Path,
        help="Path to the text file containing new contact information"
    )
    
    args = parser.parse_args()
    
    # Get YAML path from environment variable
    yaml_path = os.environ.get("CONTACTS")
    if not yaml_path:
        raise FileNotFoundError("Error: CONTACTS environment variable not set")
    yaml_path = Path(yaml_path)
    
    # Ensure text file exists
    if not args.text_file.exists():
        raise FileNotFoundError(f"Error: Text file {args.text_file} does not exist")
    
    update_contacts(yaml_path, args.text_file)


if __name__ == "__main__":
    main()
