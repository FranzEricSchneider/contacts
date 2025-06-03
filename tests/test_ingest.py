"""Unit tests for the ingest functionality."""

import unittest
from pathlib import Path
import tempfile
from typing import List

from contacts import Contact
from contacts.ingest import (
    parse_text_file,
    update_contacts,
    load_contacts,
    save_contacts,
    validate_contacts,
    validate_similar_names,
)


class TestIngest(unittest.TestCase):
    """Test cases for the ingest functionality."""

    def create_test_file(self, content: str) -> Path:
        """Create a temporary file with the given content.

        Args:
            content: The content to write to the file

        Returns:
            Path to the temporary file
        """
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write(content)
            return Path(tmp.name)

    def test_parse_text_file(self):
        """Test parsing of text file content."""
        content = """
        John Doe
        address: 2024-01-01: 123 Main St
        frequency: weekly
        update: 2024-01-01: First meeting
        characteristic: friendly
        tag: important
        url: http://example.com

        Jane Smith
        address: 2024-01-02: 456 Oak Ave
        update: 2024-01-02: Met at conference
        """

        text_file = self.create_test_file(content)

        try:
            contacts = parse_text_file(text_file)

            self.assertEqual(len(contacts), 2)

            # Check first contact
            self.assertEqual(contacts[0].name, "John Doe")
            data = dict(contacts[0].data_pairs)
            self.assertEqual(data["address"], "2024-01-01: 123 Main St")
            self.assertEqual(data["frequency"], "weekly")
            self.assertEqual(data["update"], "2024-01-01: First meeting")
            self.assertEqual(data["characteristic"], "friendly")
            self.assertEqual(data["tag"], "important")
            self.assertEqual(data["url"], "http://example.com")

            # Check line numbers
            self.assertEqual(contacts[0].name_line, 2)
            self.assertEqual(
                contacts[0].data_lines[("address", "2024-01-01: 123 Main St")], 3
            )

            # Check second contact
            self.assertEqual(contacts[1].name, "Jane Smith")
            data = dict(contacts[1].data_pairs)
            self.assertEqual(data["address"], "2024-01-02: 456 Oak Ave")
            self.assertEqual(data["update"], "2024-01-02: Met at conference")

            # Check line numbers
            self.assertEqual(contacts[1].name_line, 10)
            self.assertEqual(
                contacts[1].data_lines[("address", "2024-01-02: 456 Oak Ave")], 11
            )

        finally:
            text_file.unlink()

    def test_validate_contacts_with_errors(self):
        """Test validation of contact data with errors."""
        content = """John Doe
        address: invalid date: 123 Main St
        update: not a date: First meeting

        Jane Smith
        address: 2024/01/02: 456 Oak Ave
        """

        text_file = self.create_test_file(content)

        try:
            parsed_data = parse_text_file(text_file)
            errors = validate_contacts(parsed_data, text_file)

            self.assertEqual(len(errors), 3)  # Three invalid date formats

            # Check error messages
            self.assertTrue(any("line 2" in error for error in errors))
            self.assertTrue(any("line 3" in error for error in errors))
            self.assertTrue(any("line 6" in error for error in errors))
            self.assertTrue(any("John Doe" in error for error in errors))
            self.assertTrue(any("Jane Smith" in error for error in errors))

        finally:
            text_file.unlink()

    def test_update_contacts_with_validation_error(self):
        """Test that update_contacts raises ValueError for invalid input."""
        # Create initial YAML file
        initial_contact = Contact(name="John Doe")
        initial_contact.update_data("address", "2024-01-01: 789 Pine St")

        yaml_file = Path(tempfile.mktemp(suffix=".yaml"))
        save_contacts([initial_contact], yaml_file)

        # Create text file with invalid data
        text_content = """John Doe
        address: invalid date: 123 Main St
        """

        text_file = self.create_test_file(text_content)

        try:
            with self.assertRaises(ValueError) as cm:
                update_contacts(yaml_file, text_file)

            error_msg = str(cm.exception)
            self.assertIn("line 2", error_msg)
            self.assertIn("John Doe", error_msg)
            self.assertIn("invalid date", error_msg)

            # Verify no changes were made
            contacts = load_contacts(yaml_file)
            self.assertEqual(len(contacts), 1)
            self.assertEqual(len(contacts[0].address), 1)
            self.assertEqual(contacts[0].address[0][1], "789 Pine St")

        finally:
            yaml_file.unlink()
            text_file.unlink()

    def test_update_contacts(self):
        """Test updating contacts from text file."""
        # Create initial YAML file
        initial_contact = Contact(name="John Doe")
        initial_contact.update_data("address", "2024-01-01: 789 Pine St")
        initial_contact.update_data("frequency", "monthly")
        initial_contact.update_data("characteristic", "professional")

        yaml_file = Path(tempfile.mktemp(suffix=".yaml"))
        save_contacts([initial_contact], yaml_file)

        # Create text file with updates
        text_content = """
        John Doe
        address: 2024-01-02: 123 Main St
        frequency: weekly
        update: 2024-01-02: First meeting
        
        Jane Smith
        address: 2024-01-02: 456 Oak Ave
        update: 2024-01-02: Met at conference
        """

        text_file = self.create_test_file(text_content)

        try:
            # Update contacts
            update_contacts(yaml_file, text_file)

            # Load and verify updated contacts
            contacts = {c.name: c for c in load_contacts(yaml_file)}

            # Check John Doe updates
            john = contacts["John Doe"]
            self.assertEqual(len(john.address), 2)  # Old + new address
            self.assertEqual(john.address[0][1], "789 Pine St")
            self.assertEqual(john.address[1][1], "123 Main St")
            self.assertEqual(john.frequency, "weekly")  # Updated frequency
            self.assertEqual(len(john.update), 1)
            self.assertEqual(john.characteristic, ["professional"])

            # Check Jane Smith (new contact)
            jane = contacts["Jane Smith"]
            self.assertEqual(len(jane.address), 1)
            self.assertEqual(jane.address[0][1], "456 Oak Ave")
            self.assertEqual(len(jane.update), 1)
            self.assertEqual(jane.frequency, "")  # Default value

        finally:
            yaml_file.unlink()
            text_file.unlink()

    def test_validate_similar_names(self):
        """Test detection of similar names that might be typos."""
        # Create initial YAML file with existing contacts
        initial_contacts = [
            Contact(name="John Doe"),
            Contact(name="Jane Smith"),
            Contact(name="Robert Johnson"),
        ]

        yaml_file = Path(tempfile.mktemp(suffix=".yaml"))
        save_contacts(initial_contacts, yaml_file)

        # Test file with similar names
        text_content = """
        Jon Doe
        address: 2024-01-02: 123 Main St
        
        Jane Smyth
        address: 2024-01-02: 456 Oak Ave
        
        Robert Johnson
        address: 2024-01-02: 789 Pine St
        """

        text_file = self.create_test_file(text_content)

        try:
            with self.assertRaises(ValueError) as cm:
                update_contacts(yaml_file, text_file)

            error_msg = str(cm.exception)

            # Should catch both similar names
            self.assertIn("'Jon Doe' in", error_msg)
            self.assertIn("similar to existing 'John Doe'", error_msg)
            self.assertIn("'Jane Smyth' in", error_msg)
            self.assertIn("similar to existing 'Jane Smith'", error_msg)

            # Should not complain about identical names
            self.assertNotIn("'Robert Johnson' in", error_msg)

        finally:
            yaml_file.unlink()
            text_file.unlink()


if __name__ == "__main__":
    unittest.main()
