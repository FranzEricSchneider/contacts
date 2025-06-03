"""Unit tests for the Contact class."""

import unittest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import yaml

from contact import Contact


class TestContact(unittest.TestCase):
    """Test cases for the Contact class."""

    def setUp(self):
        """Set up test fixtures."""
        self.contact = Contact(name="Test Person")

    def test_contact_creation(self):
        """Test contact creation with default values."""
        contact = Contact(name="Empty Person")
        self.assertEqual(contact.name, "Empty Person")
        self.assertEqual(contact.address, [])
        self.assertEqual(contact.frequency, "")
        self.assertEqual(contact.update, [])
        self.assertEqual(contact.characteristic, [])
        self.assertEqual(contact.tag, [])
        self.assertEqual(contact.url, [])

    def test_to_dict(self):
        """Test conversion to and from YAML format."""
        # Add some test data
        test_date = datetime(2024, 1, 1)
        self.contact.update_data("update", "2024-01-01: Test update")
        self.contact.update_data("address", "2024-01-01: 123 Test St")
        self.contact.update_data("characteristic", "friendly")
        self.contact.update_data("tag", "test")
        self.contact.update_data("url", "http://test.com")
        self.contact.update_data("frequency", "weekly")

        # Convert to dict and back
        new_contact = Contact.from_dict(self.contact.to_dict())

        # Compare all fields
        for field in self.contact.__dataclass_fields__:
            self.assertEqual(getattr(new_contact, field), getattr(self.contact, field))

    def test_update_list_fields(self):
        """Test updating list fields (characteristic, tag, url)."""
        test_cases = [
            ("characteristic", ["organized", "punctual"]),
            ("tag", ["work", "important"]),
            ("url", ["http://example.com", "https://test.com"]),
        ]

        for field, values in test_cases:
            with self.subTest(field=field, values=values):
                # Reset contact for each subtest to ensure clean state
                self.setUp()
                for value in values:
                    self.contact.update_data(field, value)
                self.assertEqual(getattr(self.contact, field), values)

    def test_update_frequency(self):
        self.contact.update_data("frequency", "monthly")
        self.assertEqual(self.contact.frequency, "monthly")

    def test_update_dated_fields(self):
        """Test updating fields that require dates (address and update)."""
        test_cases = [
            ("address", "2024-01-01: 123 Test St", "123 Test St"),
            ("update", "2024-01-01: Initial contact", "Initial contact"),
        ]

        for field, value, expected_text in test_cases:
            with self.subTest(field=field):
                self.setUp()
                self.contact.update_data(field, value)
                dated_list = getattr(self.contact, field)
                self.assertEqual(len(dated_list), 1)
                self.assertEqual(dated_list[0][0], datetime(2024, 1, 1))
                self.assertEqual(dated_list[0][1], expected_text)

                # Test adding multiple entries
                self.contact.update_data(field, "2024-02-01: Second entry")
                dated_list = getattr(self.contact, field)
                self.assertEqual(len(dated_list), 2)
                self.assertEqual(dated_list[1][0], datetime(2024, 2, 1))
                self.assertEqual(dated_list[1][1], "Second entry")

    def test_dated_fields_with_missing_date(self):
        """Test that updating dated fields without a date raises ValueError."""
        for field in ["address", "update"]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError) as cm:
                    self.contact.update_data(field, "No date given")
                self.assertIn("must include a date", str(cm.exception))

    def test_dated_fields_with_invalid_date_format(self):
        """Test that updating dated fields with invalid date format raises ValueError."""
        for field in ["address", "update"]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError) as cm:
                    self.contact.update_data(field, "01/01/2024: Invalid format")
                self.assertIn("does not match format", str(cm.exception))

    def test_get_frequency_timedelta(self):
        """Test conversion of frequency strings to timedelta objects."""
        test_cases = [
            ("5d", timedelta(days=5)),
            ("7w", timedelta(weeks=7)),
            ("2m", timedelta(days=60)),  # 2 months * 30 days
            ("", None),  # Empty frequency
            ("invalid", None),  # Invalid format
            ("5x", None),  # Invalid unit
            ("ad", None),  # Invalid number
        ]

        for freq, expected in test_cases:
            with self.subTest(frequency=freq, expected=expected):
                self.contact.frequency = freq
                result = self.contact.get_frequency_timedelta()
                self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
