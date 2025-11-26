import shutil
import logging
from pathlib import Path

from src.config import BASE_DIR, HOSTING_PATH

class AssetCopier:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.source_assets = BASE_DIR / "assets"
        self.destination_assets = HOSTING_PATH / "assets"

    def copy_assets(self) -> None:
        self.logger.info("Copying assets to hosting directory")

        if not self.source_assets.exists():
            raise FileNotFoundError(
                f"Assets directory not found: {self.source_assets}. "
                f"Expected at: {self.source_assets.absolute()}"
            )

        try:
            shutil.copytree(
                self.source_assets,
                self.destination_assets,
                dirs_exist_ok=True
            )
            self.logger.info(f"Assets copied to {self.destination_assets}")
        except Exception as e:
            raise IOError(
                f"Failed to copy assets from {self.source_assets} "
                f"to {self.destination_assets}. Error: {e}"
            ) from e
