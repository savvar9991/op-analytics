import os
from dataclasses import dataclass


@dataclass
class InputTestData:
    """Utitlity to help manage location of data files used in tests."""

    abspath: str

    @classmethod
    def at(cls, file_path: str) -> "InputTestData":
        """Initialize at the same directory of the provided file path.

        Used in unit tests as PathManager.at(__file__)
        """
        return cls(os.path.abspath(os.path.dirname(file_path)))

    def path(self, name):
        """Return abspath for the given name on the TestCase directory."""

        return os.path.join(self.abspath, name)
