import pandas as pd
from pathlib import Path
from typing import Dict, Any

from .base import BaseDataLoader
from src.config import MEMBERS_DIR_PATH

class MemberLoader(BaseDataLoader):
    def __init__(self, logger=None):
        super().__init__(logger)
        self.members_dir = MEMBERS_DIR_PATH

    def load(self) -> Dict[str, pd.DataFrame]:
        self.logger.info(f"Loading member data from {self.members_dir}")

        if not self.members_dir.exists():
            raise FileNotFoundError(
                f"Members directory not found: {self.members_dir}. "
                f"Expected at: {self.members_dir.absolute()}. "
                f"Check that group-data repo is in correct location."
            )

        info_df = self._load_member_info()
        experiences_df = self._load_member_json_data("experiences.json")
        education_df = self._load_member_json_data("education.json")
        projects_df = self._load_member_json_data("projects.json")
        awards_df = self._load_member_json_data("awards.json")
        outreach_df = self._load_member_json_data("outreach.json")
        social_links_df = self._load_social_links()
        documents_df = self._load_member_json_data("documents.json")

        self.logger.info(
            f"Loaded data for {len(info_df)} members: "
            f"experiences={len(experiences_df)}, education={len(education_df)}, "
            f"projects={len(projects_df)}, awards={len(awards_df)}"
        )

        return {
            'info': info_df,
            'experiences': experiences_df,
            'education': education_df,
            'projects': projects_df,
            'awards': awards_df,
            'outreach': outreach_df,
            'social_links': social_links_df,
            'documents': documents_df,
        }

    def _load_member_info(self) -> pd.DataFrame:
        info_files = list(self.members_dir.glob("*/info.json"))

        if not info_files:
            raise FileNotFoundError(
                f"No member info.json files found in {self.members_dir}. "
                f"Expected at least one member directory with info.json"
            )

        info_list = []
        for info_path in info_files:
            try:
                member_data = self.load_json_file(info_path)

                if 'id' not in member_data:
                    raise ValueError(
                        f"Member info.json missing 'id' field: {info_path}"
                    )

                required_fields = ['first_name', 'last_name']
                missing_fields = [f for f in required_fields if f not in member_data]
                if missing_fields:
                    self.logger.warning(
                        f"Member {member_data.get('id', 'unknown')} missing fields: "
                        f"{', '.join(missing_fields)} in {info_path}"
                    )

                info_list.append(member_data)
            except (FileNotFoundError, ValueError) as e:
                self.logger.error(f"Failed to load member info {info_path}: {e}")

        df = pd.DataFrame(info_list).set_index("id")

        df["full_name"] = df.apply(
            lambda row: (
                row.get("nick_name", "") + " " + row["last_name"]
                if pd.notna(row.get("nick_name", ""))
                else row["first_name"] + " " + row["last_name"]
            ),
            axis=1,
        )

        return df

    def _load_member_json_data(self, filename: str) -> pd.DataFrame:
        data_list = []

        for member_dir in self.members_dir.iterdir():
            if not member_dir.is_dir():
                continue

            info_path = member_dir / "info.json"
            if not info_path.exists():
                continue

            try:
                member_info = self.load_json_file(info_path)
                member_id = member_info.get("id")

                if not member_id:
                    self.logger.warning(
                        f"Member directory {member_dir.name} has no 'id' in info.json"
                    )
                    continue

                data_path = member_dir / "jsons" / filename

                if data_path.exists():
                    data_entries = self.load_json_file(data_path)

                    if not isinstance(data_entries, list):
                        raise ValueError(
                            f"Expected list in {data_path}, got {type(data_entries)}. "
                            f"File should contain JSON array."
                        )

                    for entry in data_entries:
                        entry["id"] = member_id

                    data_list.extend(data_entries)

            except (FileNotFoundError, ValueError) as e:
                self.logger.error(
                    f"Failed to load {filename} for member {member_dir.name}: {e}"
                )

        if not data_list:
            return pd.DataFrame()

        df = pd.DataFrame(data_list).set_index("id")
        return df

    def _load_social_links(self) -> pd.DataFrame:
        social_links_list = []

        for social_link_path in self.members_dir.rglob("social_links.json"):
            try:
                member_social_link = self.load_json_file(social_link_path)

                info_path = social_link_path.parent.parent / "info.json"
                member_info = self.load_json_file(info_path)

                member_id = member_info.get("id")
                if not member_id:
                    raise ValueError(
                        f"Cannot find member ID for social links at {social_link_path}"
                    )

                member_social_link["id"] = member_id
                social_links_list.append(member_social_link)

            except (FileNotFoundError, ValueError) as e:
                self.logger.error(
                    f"Failed to load social links {social_link_path}: {e}"
                )

        if not social_links_list:
            return pd.DataFrame()

        df = pd.DataFrame(social_links_list).set_index("id")
        df.fillna("", inplace=True)

        return df
