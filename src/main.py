import sys
from pathlib import Path

from src.utils.logging_config import setup_logging
from src.data_loaders import ArticleLoader, MemberLoader, WebsiteDataLoader
from src.processors import ArticleProcessor, MemberProcessor
from src.renderers import (
    HomepageRenderer,
    ContactPageRenderer,
    SupportPageRenderer,
    JoinUsPageRenderer,
    CurrentMembersRenderer,
    AlumniMembersRenderer,
    IndividualMemberRenderer,
    ResearchFrontPageRenderer,
    SubResearchFrontPageRenderer,
    IndividualResearchPageRenderer,
    NewsFrontPageRenderer,
    IndividualNewsPageRenderer,
    GalleryPageRenderer,
    AssetCopier
)

class SiteGenerator:
    def __init__(self, log_level: str = "INFO"):
        self.logger = setup_logging(log_level)
        self.data = {}
        self.logger.info("="*80)
        self.logger.info("Website Generator Started")
        self.logger.info("="*80)

    def load_articles(self) -> None:
        loader = ArticleLoader(self.logger)
        self.data['articles_df'] = loader.load()

        if self.data['articles_df'].empty:
            raise ValueError("No articles loaded. Cannot proceed with site generation.")

    def load_members(self) -> None:
        loader = MemberLoader(self.logger)
        member_data = loader.load()

        self.data['member_info_df'] = member_data['info']
        self.data['experiences_df'] = member_data['experiences']
        self.data['education_df'] = member_data['education']
        self.data['projects_df'] = member_data['projects']
        self.data['awards_df'] = member_data['awards']
        self.data['outreach_df'] = member_data['outreach']
        self.data['social_links_df'] = member_data['social_links']
        self.data['documents_df'] = member_data['documents']

        if self.data['member_info_df'].empty:
            raise ValueError("No members loaded. Cannot proceed with site generation.")

    def load_website_data(self) -> None:
        loader = WebsiteDataLoader(self.logger)
        website_data = loader.load()

        self.data['general'] = website_data['general']
        self.data['homepage'] = website_data['homepage']
        self.data['contact'] = website_data['contact']
        self.data['research'] = website_data['research']
        self.data['support'] = website_data['support']
        self.data['opportunities'] = website_data['opportunities']
        self.data['role_hierarchy'] = website_data['role_hierarchy']

        self.data['gallery_events'] = loader.load_gallery_events()

    def process_article_categories(self) -> None:
        processor = ArticleProcessor(self.logger)

        news_df, research_df = processor.split_by_category(self.data['articles_df'])
        self.data['news_df'] = news_df
        self.data['research_df'] = research_df

        self.data['recent_content_df'] = processor.get_recent_content_by_category(
            self.data['articles_df']
        )

    def process_member_roles(self) -> None:
        processor = MemberProcessor(self.logger)

        current_df, alumni_df = processor.process_member_status(
            self.data['member_info_df'],
            self.data['experiences_df'],
            self.data['education_df'],
            self.data['projects_df']
        )

        self.data['current_members_df'] = processor.sort_by_role_hierarchy(
            current_df,
            self.data['role_hierarchy']
        )
        self.data['alumni_members_df'] = alumni_df

        self.data['info_dict'] = self.data['member_info_df'].to_dict('index')

        self.data['education_grouped'] = processor.group_dataframe_by_id(
            self.data['education_df']
        )
        self.data['experiences_grouped'] = processor.group_dataframe_by_id(
            self.data['experiences_df']
        )
        self.data['projects_grouped'] = processor.group_dataframe_by_id(
            self.data['projects_df']
        )
        self.data['awards_grouped'] = processor.group_dataframe_by_id(
            self.data['awards_df']
        )
        self.data['outreach_grouped'] = processor.group_dataframe_by_id(
            self.data['outreach_df']
        )

        article_processor = ArticleProcessor(self.logger)
        self.data['news_df'] = article_processor.process_news_content_links(
            self.data['news_df'],
            self.data['member_info_df'],
            self.data['current_members_df']
        )

    def run(self) -> None:
        stages = [
            ("Load Articles", self.load_articles),
            ("Load Member Data", self.load_members),
            ("Load Website Configuration", self.load_website_data),
            ("Process Article Categories", self.process_article_categories),
            ("Process Member Roles", self.process_member_roles),
            ("Render Homepage", self.render_homepage),
            ("Render Contact Page", self.render_contact),
            ("Render Support Page", self.render_support),
            ("Render Join Us Page", self.render_join_us),
            ("Render Member Pages", self.render_member_pages),
            ("Render Research Pages", self.render_research_pages),
            ("Render News Pages", self.render_news_pages),
            ("Render Gallery Page", self.render_gallery),
            ("Copy Assets", self.copy_assets),
        ]

        total_stages = len(stages)

        for idx, (stage_name, stage_fn) in enumerate(stages, 1):
            self.logger.info("")
            self.logger.info(f"[{idx}/{total_stages}] Starting: {stage_name}")
            self.logger.info("-" * 80)

            try:
                stage_fn()
                self.logger.info(f"✓ Completed: {stage_name}")
            except Exception as e:
                self.logger.error(f"✗ Failed: {stage_name}")
                self.logger.error(f"Error: {e}")
                self.logger.exception("Full traceback:")
                sys.exit(1)

        self.logger.info("")
        self.logger.info("="*80)
        self.logger.info("Website Generation Complete!")
        self.logger.info("="*80)
