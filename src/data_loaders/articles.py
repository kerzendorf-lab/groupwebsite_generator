import pandas as pd
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any

from .base import BaseDataLoader
from src.config import ARTICLE_DIR_PATH, ARTICLE_IMAGE_DESTINATION_DIR
from src.utils.path_helpers import set_new_image_path

class ArticleLoader(BaseDataLoader):
    def __init__(self, logger=None):
        super().__init__(logger)
        self.article_dir = ARTICLE_DIR_PATH
        self.image_dest_dir = ARTICLE_IMAGE_DESTINATION_DIR

    def load(self) -> pd.DataFrame:
        self.logger.info(f"Loading articles from {self.article_dir}")

        if not self.article_dir.exists():
            raise FileNotFoundError(
                f"Article directory not found: {self.article_dir}. "
                f"Expected at: {self.article_dir.absolute()}. "
                f"Check that research_news repo is in correct location."
            )

        article_content_list = []
        today = date.today()
        today_datetime = datetime.combine(today, datetime.min.time())

        info_files = list(self.article_dir.rglob('info.json'))
        self.logger.info(f"Found {len(info_files)} article info.json files")

        for content_file_path in info_files:
            try:
                article_content = self._load_single_article(
                    content_file_path,
                    today_datetime
                )
                if article_content:
                    article_content_list.append(article_content)
            except Exception as e:
                self.logger.error(
                    f"Failed to load article {content_file_path.parent.name}: {e}"
                )

        if not article_content_list:
            self.logger.warning("No articles loaded successfully")
            return pd.DataFrame()

        df = pd.DataFrame(article_content_list)
        df = self._process_article_dataframe(df)

        self.logger.info(
            f"Successfully loaded {len(df)} articles "
            f"({len(df[df['category'] == 'News'])} news, "
            f"{len(df[df['category'] != 'News'])} research)"
        )

        return df

    def _load_single_article(
        self,
        content_file_path: Path,
        today_datetime: datetime
    ) -> Dict[str, Any] | None:
        article_content = self.load_json_file(content_file_path)

        required_fields = ['date', 'platforms', 'cover_image', 'content', 'category']
        missing_fields = [f for f in required_fields if f not in article_content]
        if missing_fields:
            raise ValueError(
                f"Article {content_file_path.parent.name} missing required fields: "
                f"{', '.join(missing_fields)}. "
                f"File: {content_file_path}"
            )

        article_date = datetime.strptime(article_content["date"], "%m-%d-%Y")

        if "kg" not in article_content["platforms"]:
            self.logger.debug(
                f"Skipping {content_file_path.parent.name}: 'kg' not in platforms"
            )
            return None

        if article_date > today_datetime:
            self.logger.debug(
                f"Skipping {content_file_path.parent.name}: "
                f"future date {article_content['date']}"
            )
            return None

        image_path = Path(article_content["cover_image"])
        article_content["cover_image"] = set_new_image_path(
            content_file_path,
            image_path,
            self.image_dest_dir
        )

        for content_key, content_value in article_content["content"].items():
            if "img" in content_key:
                new_content_value = set_new_image_path(
                    content_file_path,
                    Path(content_value),
                    self.image_dest_dir
                )
                article_content["content"][content_key] = new_content_value

        return article_content

    def _process_article_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df["date"] = pd.to_datetime(df["date"], format="%m-%d-%Y")

        df["cover_image_height"] = (
            df["cover_image_height"].fillna("330px").replace("", "330px")
        )
        df["cover_image_width"] = (
            df["cover_image_width"].fillna("520px").replace("", "520px")
        )

        df["category"] = df["category"].replace("Overview", "Computational Metascience")

        df['image_name'] = df['cover_image'].apply(lambda x: Path(x).name)

        return df
