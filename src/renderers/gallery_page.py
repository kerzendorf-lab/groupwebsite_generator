import shutil
import pandas as pd
from pathlib import Path
from PIL import Image
from typing import List, Dict, Any

from .base import BasePageRenderer
from src.config import HOSTING_PATH, GALLERY_CONTENT_SOURCE

class GalleryPageRenderer(BasePageRenderer):
    def render(self, general, info_dict, gallery_events: List[tuple]) -> None:
        self.logger.info("Rendering gallery page")

        processed_events = []

        for event_file, event_data in gallery_events:
            try:
                processed_event = self._process_gallery_event(event_file, event_data)
                processed_events.append(processed_event)
            except Exception as e:
                self.logger.error(
                    f"Failed to process gallery event {event_data.get('event_id', 'unknown')}: {e}"
                )

        if "date" in processed_events[0] if processed_events else {}:
            for event in processed_events:
                event["date"] = pd.to_datetime(event["date"])

        self.render_page(
            "gallery.html.j2",
            "Gallery.html",
            general=general,
            member_data=info_dict,
            events=processed_events
        )

        self.logger.info(f"Rendered gallery page with {len(processed_events)} events")

    def _process_gallery_event(self, event_file: Path, event_data: Dict[str, Any]) -> Dict[str, Any]:
        event_id = event_data.get("event_id", "unknown_event")

        dest_image_dir = (
            HOSTING_PATH / "website_files" / "images" /
            "gallery" / event_id / "media" / "images"
        )
        dest_image_dir.mkdir(parents=True, exist_ok=True)

        source_image_dir = event_file.parent / "media" / "images"
        if source_image_dir.exists():
            shutil.copytree(source_image_dir, dest_image_dir, dirs_exist_ok=True)
        else:
            self.logger.warning(
                f"No images directory found for event {event_id} at {source_image_dir}"
            )

        for image in event_data.get("images", []):
            image_path = GALLERY_CONTENT_SOURCE / event_id / image["image_path"]

            if not image_path.exists():
                self.logger.warning(
                    f"Image not found: {image_path} for event {event_id}"
                )
                continue

            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    new_width = int(width * 0.7)
                    new_height = int(height * 0.7)

                    image["scaled_width"] = new_width
                    image["scaled_height"] = new_height
            except Exception as e:
                self.logger.error(
                    f"Failed to process image {image_path}: {e}"
                )

        return event_data
