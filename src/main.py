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
