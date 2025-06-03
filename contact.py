"""Contact class for managing contact information."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple
import yaml
from pathlib import Path


@dataclass
class Contact:
    """A class representing a contact with various attributes."""
    name: str
    address: List[Tuple[datetime, str]] = field(default_factory=list)
    frequency: str = ""
    update: List[Tuple[datetime, str]] = field(default_factory=list)
    characteristic: List[str] = field(default_factory=list)
    tag: List[str] = field(default_factory=list)
    url: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Contact":
        """Create a Contact instance from a dictionary."""
        # Convert lists to tuples for dated fields
        for field in ["update", "address"]:
            if field in data:
                # Convert date strings back to datetime objects
                data[field] = [
                    (datetime.strptime(item[0], "%Y-%m-%d"), item[1])
                    for item in data[field]
                ]
        return cls(**data)

    def to_dict(self) -> dict:
        """Convert the Contact to a YAML-compatible dictionary."""
        def format_dated_item(item: Tuple[datetime, str]) -> List[str]:
            """Format a dated item for YAML output."""
            return [item[0].strftime("%Y-%m-%d"), item[1]]

        return {
            "name": self.name,
            "address": [format_dated_item(item) for item in self.address],
            "frequency": self.frequency,
            "update": [format_dated_item(item) for item in self.update],
            "characteristic": self.characteristic,
            "tag": self.tag,
            "url": self.url
        }

    def _parse_dated_value(self, value: str) -> Tuple[datetime, str]:
        """Parse a dated value in the format 'YYYY-MM-DD: text'."""
        try:
            date_str, text = value.split(":", 1)
        except ValueError:
            raise ValueError("Value must include a date in the format '%Y-%m-%d: text'")
        
        date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return date, text.strip()

    def update_data(self, key: str, value: str) -> None:
        """Update contact information based on key-value pair."""
        if key in ("characteristic", "tag", "url"):
            # Append to simple list fields
            getattr(self, key).append(value)
        elif key == "frequency":
            # Update non-list field
            self.frequency = value
        elif key in ("update", "address"):
            # Parse and append dated value
            date, text = self._parse_dated_value(value)
            getattr(self, key).append((date, text))
        else:
            raise ValueError(f"Invalid key: {key}")
