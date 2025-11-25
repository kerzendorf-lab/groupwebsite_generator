import pandas as pd
from typing import Dict, Any

from .base import BasePageRenderer
from src.config import INDIVIDUAL_MEMBER_SECTION_MAP

class CurrentMembersRenderer(BasePageRenderer):
    def render(self, general, current_members, social_links) -> None:
        self.logger.info("Rendering current members page")

        self.render_page(
            "current_members.html.j2",
            "current_members.html",
            general=general,
            current_members=current_members,
            socials=social_links.to_dict("index") if not social_links.empty else {}
        )

class AlumniMembersRenderer(BasePageRenderer):
    def render(self, general, alumni_members) -> None:
        self.logger.info("Rendering alumni members page")

        self.render_page(
            "alumni_members.html.j2",
            "alumni_members.html",
            general=general,
            alumni_members=alumni_members,
        )

class IndividualMemberRenderer(BasePageRenderer):
    def render(
        self,
        general,
        info_df: pd.DataFrame,
        social_links_df: pd.DataFrame,
        documents_df: pd.DataFrame,
        education_grouped: Dict[str, Any],
        experience_grouped: Dict[str, Any],
        projects_grouped: Dict[str, Any],
        awards_grouped: Dict[str, Any],
        outreach_grouped: Dict[str, Any],
        article_content_df: pd.DataFrame
    ) -> None:
        self.logger.info(f"Rendering {len(info_df)} individual member pages")

        socials_dict = social_links_df.to_dict("index") if not social_links_df.empty else {}
        documents_dict = documents_df.to_dict("index") if not documents_df.empty else {}
        content_dict = article_content_df.to_dict("index") if not article_content_df.empty else {}

        for person_id, person_data in info_df.iterrows():
            self.render_page(
                "individual_person.html.j2",
                f"members/{person_id}/{person_id}.html",
                general=general,
                member_id=person_id,
                member_data=person_data,
                socials=socials_dict,
                documents=documents_dict,
                education=education_grouped,
                experience=experience_grouped,
                projects=projects_grouped,
                awards=awards_grouped,
                outreach=outreach_grouped,
                section_headings=INDIVIDUAL_MEMBER_SECTION_MAP,
                content=content_dict,
            )

        self.logger.info(f"Rendered {len(info_df)} member pages")
