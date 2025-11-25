from pathlib import Path
from typing import Dict, Any

from .base import BaseDataLoader
from src.config import (
    WEBSITE_DATA_PATH,
    OPPORTUNITIES_PATH,
    ROLE_HIERARCHY_PATH,
    GALLERY_CONTENT_SOURCE
)

class WebsiteDataLoader(BaseDataLoader):
    def __init__(self, logger=None):
        super().__init__(logger)
        self.website_data_path = WEBSITE_DATA_PATH

    def load(self) -> Dict[str, Any]:
        self.logger.info("Loading website configuration data")

        if not self.website_data_path.exists():
            raise FileNotFoundError(
                f"Website data directory not found: {self.website_data_path}. "
                f"Expected at: {self.website_data_path.absolute()}"
            )

        data = {
            'general': self._load_website_json('general.json'),
            'homepage': self._load_website_json('homepage.json'),
            'contact': self._load_website_json('contact.json'),
            'research': self._load_website_json('research_categories.json'),
            'support': self._load_website_json('support.json'),
            'opportunities': self._load_json_with_path(OPPORTUNITIES_PATH),
            'role_hierarchy': self._load_json_with_path(ROLE_HIERARCHY_PATH),
        }

        self.logger.info("Successfully loaded all website configuration data")

        return data

    def _load_website_json(self, filename: str) -> Dict[str, Any]:
        file_path = self.website_data_path / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required website data file not found: {filename}. "
                f"Expected at: {file_path}. "
                f"This file is required for site generation."
            )

        return self.load_json_file(file_path)

    def _load_json_with_path(self, file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found: {file_path}. "
                f"Expected at: {file_path.absolute()}"
            )

        return self.load_json_file(file_path)

    def load_gallery_events(self) -> list:
        self.logger.info("Loading gallery events")

        if not GALLERY_CONTENT_SOURCE.exists():
            self.logger.warning(
                f"Gallery content directory not found: {GALLERY_CONTENT_SOURCE}"
            )
            return []

        events = []
        event_files = list(GALLERY_CONTENT_SOURCE.rglob("info.json"))

        for event_file in event_files:
            try:
                event_data = self.load_json_file(event_file)

                if "event_id" not in event_data:
                    raise ValueError(
                        f"Gallery event missing 'event_id': {event_file}"
                    )

                events.append((event_file, event_data))
            except (FileNotFoundError, ValueError) as e:
                self.logger.error(f"Failed to load gallery event {event_file}: {e}")

        self.logger.info(f"Loaded {len(events)} gallery events")

        return events
