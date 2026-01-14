import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Configuration - Edit this to switch between websites
CONFIG_FILE = "config_dti.json"  # or "config_dti.json"

# CONFIG_FILE = "config_lab.json"
# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / CONFIG_FILE
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)
CONFIG_DIR = CONFIG_PATH.parent

# Constants - resolve paths relative to config directory
GROUP_DATA_DIR = (CONFIG_DIR / config["paths"]["group_data_dir"]).resolve()
MEMBERS_DIR_PATH = GROUP_DATA_DIR / "members/"
WEBSITE_DATA_PATH = GROUP_DATA_DIR / "website_data/"
ROLE_HIERARCHY_PATH = WEBSITE_DATA_PATH / "role_hierarchy.json"

# Lab member data fallback (for DTI website)
LAB_GROUP_DATA_DIR = None
LABMEMBERS_JSON_PATH = None
if "lab_group_data" in config["paths"]:
    LAB_GROUP_DATA_DIR = (CONFIG_DIR / config["paths"]["lab_group_data"]).resolve()
if "labmembers_json" in config["paths"]:
    LABMEMBERS_JSON_PATH = (CONFIG_DIR / config["paths"]["labmembers_json"]).resolve()

GROUP_FILTER = config.get("group_filter", ["DTI", "TARDIS", "kerzendorf"])
INSTITUTION_FILTER = config.get("institution_filter", "Michigan State University")


class MemberDataLoader:
    def __init__(self, members_dir: Path = MEMBERS_DIR_PATH):
        self.members_dir = members_dir

    def _load_records(self, jsons_dir, filename, member_id):
        path = jsons_dir / filename
        if not path.exists():
            return []
        records = json.loads(path.read_text())
        for record in records:
            record['member_id'] = member_id
        return records

    def _parse_dates(self, records, date_fields, member_id=None):
        for record in records:
            for field in date_fields:
                if field not in record:
                    continue

                if not record[field]:
                    record[field] = pd.NaT
                    continue

                try:
                    record[field] = pd.to_datetime(record[field])
                except ValueError as e:
                    if member_id:
                        print(e, member_id)
        return records

    def load_all_data(self):
        data_types = ['education', 'experiences', 'projects', 'awards', 'outreach', 'documents', 'posters', 'publications']
        data_config = {dt: f"{dt}.json" for dt in data_types}
        data = {key: [] for key in data_config}

        start_end_dates = ['education.json', 'experiences.json', 'projects.json', 'outreach.json']
        single_date_with_errors = ['publications.json']
        dual_date_format = ['awards.json']

        members_data = []

        # Check if we should use labmembers.json
        member_ids_to_load = None
        use_lab_members_dir = False
        if LABMEMBERS_JSON_PATH and LABMEMBERS_JSON_PATH.exists():
            labmembers_data = json.loads(LABMEMBERS_JSON_PATH.read_text())
            member_ids_to_load = set(labmembers_data["members"])
            # If labmembers.json exists and lab data dir is specified, load from lab dir
            if LAB_GROUP_DATA_DIR:
                use_lab_members_dir = True

        # Determine which members directory to use
        search_dir = LAB_GROUP_DATA_DIR / "members" if use_lab_members_dir else self.members_dir

        for member_dir in search_dir.glob("*"):
            if not member_dir.is_dir():
                continue
            info_path = member_dir / "info.json"
            if not info_path.exists():
                continue
            member_info = json.loads(info_path.read_text())
            member_id = member_info["id"]

            # If labmembers.json exists, only load specified members
            if member_ids_to_load and member_id not in member_ids_to_load:
                continue

            full_name = (
                f"{member_info.get('nick_name', member_info.get('first_name', ''))} {member_info.get('last_name', '')}"
                if member_info.get('nick_name')
                else f"{member_info.get('first_name', '')} {member_info.get('last_name', '')}"
            )
            member_info['full_name'] = full_name.strip()

            jsons_dir = member_dir / "jsons"

            social_path = jsons_dir / "social_links.json"
            if social_path.exists():
                social_data = json.loads(social_path.read_text())
                member_info.update(social_data)

            members_data.append(member_info)

            for key, filename in data_config.items():
                records = self._load_records(jsons_dir, filename, member_id)
                if filename in start_end_dates:
                    records = self._parse_dates(records, ['start_date', 'end_date'])
                elif filename in single_date_with_errors:
                    records = self._parse_dates(records, ['date'], member_id)
                elif filename in dual_date_format:
                    records = self._parse_dates(records, ['date', 'start_date', 'end_date'], member_id)
                data[key].extend(records)

        members_df = pd.DataFrame(members_data).set_index('id')
        self.members_df = members_df

        for key in data:
            if data[key]:
                df = pd.DataFrame(data[key]).set_index('member_id')
            else:
                df = pd.DataFrame()
            setattr(self, f"{key}_df", df)


class CurrentMemberProcessor:
    def __init__(self, members_df, education_df, experiences_df, projects_df):
        self.members_df = members_df
        self.education_df = education_df
        self.experiences_df = experiences_df
        self.projects_df = projects_df

        with open(ROLE_HIERARCHY_PATH, "r") as file_name:
            self.role_hierarchy = json.load(file_name)

    def process_education(self):
        """Get most recent education and determine academic role"""
        def most_recent_row(group):
            sorted_group = group.sort_values(by=['start_date', 'end_date'], ascending=[False, True])
            return sorted_group.iloc[0:1]

        self.edu_most_recent = self.education_df.groupby(level=0).apply(most_recent_row).droplevel(0)

        self.edu_most_recent['academic_role'] = ""
        msu_mask = self.edu_most_recent['institution'] == INSTITUTION_FILTER
        bachelors_mask = msu_mask & (self.edu_most_recent['degree'] == "Bachelors")
        grad_mask = msu_mask & (self.edu_most_recent['degree'].isin(["PhD", "Masters"]))

        self.edu_most_recent.loc[bachelors_mask, 'academic_role'] = "Undergraduate Student"
        self.edu_most_recent.loc[grad_mask, 'academic_role'] = "Graduate Student"

    def process_experiences(self):
        """Get most recent experience per member"""
        self.experiences_df = self.experiences_df.fillna("")

        def most_recent_row(group):
            sorted_group = group.sort_values(by=['start_date', 'end_date'], ascending=[False, True])
            relevant_group = sorted_group[sorted_group['group'].str.contains('|'.join(GROUP_FILTER))]
            return relevant_group.iloc[0:1] if not relevant_group.empty else sorted_group.iloc[0:1]

        self.exp_most_recent = self.experiences_df.groupby(level=0).apply(most_recent_row).droplevel(0)

    def _merge_edu_exp(self):
        """Merge education and experience dataframes"""
        exp_suffixed = self.exp_most_recent.add_suffix('_exp')
        edu_suffixed = self.edu_most_recent.add_suffix('_edu')
        return exp_suffixed.merge(edu_suffixed, left_index=True, right_index=True, how='outer')

    def _determine_status_and_role(self, row):
        """Determine if member is current and their role"""
        if row['institution_edu'] == INSTITUTION_FILTER:
            is_current_edu = pd.isna(row['end_date_edu']) or row['end_date_edu'] >= datetime.now()
            has_ended_exp = pd.notna(row['end_date_exp'])
            is_current = is_current_edu and not has_ended_exp

            if row['academic_role_edu']:
                current_role = row['academic_role_edu']
            else:
                current_role = row['role_exp']

            return pd.Series({'isCurrent': is_current, 'current_role': current_role})
        elif row['group_exp'] in GROUP_FILTER and (pd.isna(row['end_date_exp']) or row['end_date_exp'] >= datetime.now()):
            return pd.Series({'isCurrent': True, 'current_role': row['role_exp']})
        else:
            current_role = row['academic_role_edu'] if row['academic_role_edu'] else row['role_exp']
            return pd.Series({'isCurrent': False, 'current_role': current_role})

    def _add_projects(self, df):
        """Add current project titles to members"""
        df["current_project_title"] = ""

        common_members = df.index.intersection(self.projects_df.index)
        projects_first = self.projects_df.loc[common_members].groupby(level=0).first()
        df.loc[common_members, "current_project_title"] = projects_first["project_title"]

    def _sort_by_hierarchy(self, df):
        """Sort members by role hierarchy"""
        df['rank'] = df['current_role'].map(self.role_hierarchy)
        df = df.sort_values(by='rank')
        return df.drop(columns='rank')

    def merge_and_determine_status(self):
        """Merge edu/exp and determine current vs alumni status"""
        merged = self._merge_edu_exp()
        status_role = merged.apply(self._determine_status_and_role, axis=1)
        merged = pd.concat([merged, status_role], axis=1)

        self.current_members = merged[merged['isCurrent']][["current_role"]]
        self.alumni_members = merged[~merged['isCurrent']][["current_role"]]

        self.current_members_with_info = pd.merge(self.current_members, self.members_df, left_index=True, right_index=True, how='inner')
        self.alumni_members_with_info = pd.merge(self.alumni_members, self.members_df, left_index=True, right_index=True, how='inner')[['current_role', 'full_name']]

        self._add_projects(self.current_members_with_info)
        self.current_members_with_info = self._sort_by_hierarchy(self.current_members_with_info)

    def process(self):
        """Run full pipeline"""
        self.process_education()
        self.process_experiences()
        self.merge_and_determine_status()


# Load member data
loader = MemberDataLoader()
loader.load_all_data()

print(f"Members: {len(loader.members_df)}")
print(f"Education records: {len(loader.education_df)}")
print(f"Experiences records: {len(loader.experiences_df)}")
print(f"Projects records: {len(loader.projects_df)}")

# Process current and alumni members
processor = CurrentMemberProcessor(loader.members_df, loader.education_df, loader.experiences_df, loader.projects_df)
processor.process()

# Add academic role and project info to members_df
loader.members_df["academic_role"] = ""
loader.members_df["current_project_title"] = ""

loader.members_df.loc[processor.current_members_with_info.index, "academic_role"] = processor.current_members_with_info["current_role"]
loader.members_df.loc[processor.current_members_with_info.index, "current_project_title"] = processor.current_members_with_info["current_project_title"]

alumni_only = processor.alumni_members_with_info.index.difference(processor.current_members_with_info.index)
loader.members_df.loc[alumni_only, "academic_role"] = processor.alumni_members_with_info.loc[alumni_only, "current_role"]

processor.alumni_members_with_info = processor.alumni_members_with_info.replace("nan", pd.NA).fillna("")

# Save to CSV
loader.members_df.to_csv("members.csv")
processor.current_members_with_info.to_csv("current_members.csv")
processor.alumni_members_with_info.to_csv("alumni_members.csv")
loader.education_df.to_csv("education.csv")
loader.experiences_df.to_csv("experiences.csv")
loader.projects_df.to_csv("projects.csv")
loader.awards_df.to_csv("awards.csv")
loader.outreach_df.to_csv("outreach.csv")
loader.documents_df.to_csv("documents.csv")

print(f"Saved members.csv ({len(loader.members_df)} members)")
print(f"Saved current_members.csv ({len(processor.current_members_with_info)} current members)")
print(f"Saved alumni_members.csv ({len(processor.alumni_members_with_info)} alumni members)")
