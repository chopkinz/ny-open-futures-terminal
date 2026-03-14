"""Session time windows (NY time)."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SessionWindow:
    """Time window in HH:MM format (America/New_York)."""
    start: str
    end: str

    def __post_init__(self):
        self.start = self.start.strip()
        self.end = self.end.strip()


# Default windows
OVERNIGHT = SessionWindow("18:00", "04:00")   # prior day 18:00 to 04:00
PREMARKET = SessionWindow("04:00", "09:29")
NY_OPEN = "09:30"
STUDY_WINDOW_END = "12:00"
