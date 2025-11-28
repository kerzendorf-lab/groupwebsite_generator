import json
import logging
from pathlib import Path
from typing import Any, Dict, List
from abc import ABC, abstractmethod

class BaseDataLoader(ABC):
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def load_json_file(self, file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            raise FileNotFoundError(
                f"JSON file not found: {file_path}. "
                f"Expected at: {file_path.absolute()}"
            )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.debug(f"Successfully loaded JSON: {file_path.name}")
            return data
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in file: {file_path}. "
                f"Error at line {e.lineno}, column {e.colno}: {e.msg}. "
                f"Check file syntax at {file_path.absolute()}"
            ) from e
        except UnicodeDecodeError as e:
            raise ValueError(
                f"Encoding error in file: {file_path}. "
                f"File must be UTF-8 encoded. Error: {e}"
            ) from e

    def load_json_files(self, pattern: str, base_path: Path) -> List[Dict[str, Any]]:
        files = list(base_path.rglob(pattern))

        if not files:
            self.logger.warning(
                f"No files matching pattern '{pattern}' found in {base_path}"
            )
            return []

        data_list = []
        failed_files = []

        for file_path in files:
            try:
                data = self.load_json_file(file_path)
                data_list.append(data)
            except (FileNotFoundError, ValueError) as e:
                failed_files.append((file_path, str(e)))
                self.logger.error(f"Failed to load {file_path}: {e}")

        if failed_files:
            self.logger.warning(
                f"Failed to load {len(failed_files)} files. "
                f"Loaded {len(data_list)} successfully."
            )

        return data_list

    @abstractmethod
    def load(self) -> Any:
        pass
