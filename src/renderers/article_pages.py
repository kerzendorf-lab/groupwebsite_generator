import pandas as pd
from typing import Dict, Any

from .base import BasePageRenderer
from src.config import SUB_RESEARCH_PATH
from src.utils.path_helpers import page_link

class ResearchFrontPageRenderer(BasePageRenderer):
    def render(self, general, research_content_df, research_data, info_dict) -> None:
        self.logger.info("Rendering research front page")

        self.render_page(
            "research.html.j2",
            "Research.html",
            general=general,
            content=research_content_df,
            research=research_data,
            current_members=info_dict,
        )

class SubResearchFrontPageRenderer(BasePageRenderer):
    def render(self, general, research_data, research_content_df, info_dict) -> None:
        self.logger.info("Rendering sub-research front pages")

        SUB_RESEARCH_PATH.mkdir(parents=True, exist_ok=True)

        categories = research_content_df.loc[
            research_content_df.category != "News", "category"
        ].unique()

        for category in categories:
            self.render_page(
                "sub_research_frontpage.html.j2",
                f"sub_research/{page_link(category.lower())}.html",
                general=general,
                research=research_data,
                content=research_content_df,
                category=category,
                current_members=info_dict,
            )

        self.logger.info(f"Rendered {len(categories)} sub-research front pages")

class IndividualResearchPageRenderer(BasePageRenderer):
    def render(self, general, research_content_df, info_dict) -> None:
        self.logger.info(f"Rendering {len(research_content_df)} individual research pages")

        for index, row in research_content_df.iterrows():
            category_path = page_link(row.category.lower())
            article_path = page_link(row.article_id.lower())

            if row['category'] == "Software":
                destination_path = f"sub_research/{article_path}.html"
            else:
                destination_path = f"sub_research/{category_path}/{article_path}.html"

                folder_path = SUB_RESEARCH_PATH / category_path
                folder_path.mkdir(parents=True, exist_ok=True)

            self.render_page(
                "research_page_no_twitter.html.j2",
                destination_path,
                general=general,
                content=row,
                member_data=info_dict,
                article_id=row["article_id"],
            )

        self.logger.info(f"Rendered {len(research_content_df)} research pages")

class NewsFrontPageRenderer(BasePageRenderer):
    def render(self, general, news_content_df, info_dict) -> None:
        self.logger.info("Rendering news front page")

        self.render_page(
            "news.html.j2",
            "News.html",
            general=general,
            content=news_content_df,
            category="News",
            member_data=info_dict,
        )

class IndividualNewsPageRenderer(BasePageRenderer):
    def render(self, general, news_content_df, info_dict) -> None:
        self.logger.info(f"Rendering {len(news_content_df)} individual news pages")

        for index, row in news_content_df.iterrows():
            article_path = page_link(row.article_id.lower())

            self.render_page(
                "news_page_no_twitter.html.j2",
                f"news/{article_path}.html",
                general=general,
                content=row,
                member_data=info_dict,
                category="News"
            )

        self.logger.info(f"Rendered {len(news_content_df)} news pages")
