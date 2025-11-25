import pandas as pd
import logging
import re
from pathlib import Path

class ArticleProcessor:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def split_by_category(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        self.logger.info("Splitting articles by category")

        news_df = df[
            (df["category"] == "News") |
            (df["tags"].apply(
                lambda x: "news" in x if isinstance(x, list) else False
            ))
        ].sort_values(by=["date"], ascending=[False])

        research_df = df[
            df["category"] != "News"
        ].sort_values(by=["category", "date"], ascending=[True, False])

        self.logger.info(
            f"Split into {len(news_df)} news articles and "
            f"{len(research_df)} research articles"
        )

        return news_df, research_df

    def get_recent_content_by_category(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info("Getting most recent article per category")

        sorted_df = df.sort_values(
            by=["category", "date"],
            ascending=[True, False]
        )

        recent = sorted_df.groupby("category").head(1).copy()

        self.logger.info(f"Found {len(recent)} recent articles across categories")

        return recent

    def urlize_content(
        self,
        content: str,
        info_df: pd.DataFrame,
        current_members_df: pd.DataFrame
    ) -> str:
        def replace_id(match):
            member_id = match.group(1)

            if member_id in info_df.index:
                name = info_df.loc[member_id, 'full_name']

                if member_id in current_members_df.index:
                    return (
                        f'<a href="../members/{member_id}/{member_id}.html" '
                        f'target="_blank">{name}</a>'
                    )
                else:
                    return name
            else:
                return member_id.replace('_', ' ').title()

        return re.sub(r'\[(\w+)\]', replace_id, content)

    def process_news_content_links(
        self,
        news_df: pd.DataFrame,
        info_df: pd.DataFrame,
        current_members_df: pd.DataFrame
    ) -> pd.DataFrame:
        self.logger.info("Processing member links in news content")

        df_copy = news_df.copy()

        for index, row in df_copy.iterrows():
            content = row['content']
            for content_key in content:
                if "para" in content_key:
                    content[content_key] = self.urlize_content(
                        content[content_key],
                        info_df,
                        current_members_df
                    )

        return df_copy
