import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any

from src.config import (
    GROUP_FILTER,
    INSTITUTION_FILTER,
    ROLE_MAP,
    DEGREE_MAP
)

class MemberProcessor:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def process_member_status(
        self,
        info_df: pd.DataFrame,
        exp_df: pd.DataFrame,
        edu_df: pd.DataFrame,
        projects_df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        self.logger.info("Processing member current/alumni status")

        exp_processed = self._prepare_experiences(exp_df)
        edu_processed = self._prepare_education(edu_df)

        merged_df = self._merge_education_experience(exp_processed, edu_processed)
        merged_df = self._determine_current_status(merged_df)

        current_df = merged_df[merged_df['isCurrent']].copy()
        alumni_df = merged_df[~merged_df['isCurrent']].copy()

        current_with_info = self._add_member_info(
            current_df,
            info_df,
            projects_df
        )
        alumni_with_info = self._add_alumni_info(alumni_df, info_df)

        self.logger.info(
            f"Classified {len(current_with_info)} current members and "
            f"{len(alumni_with_info)} alumni"
        )

        return current_with_info, alumni_with_info

    def _prepare_experiences(self, exp_df: pd.DataFrame) -> pd.DataFrame:
        if exp_df.empty:
            return pd.DataFrame()

        df = exp_df.copy()
        df['end_date'] = pd.to_datetime(df['end_date'], format='%Y-%m-%d', errors='coerce')
        df['start_date'] = pd.to_datetime(df['start_date'], format='%Y-%m-%d', errors='coerce')
        df.fillna("", inplace=True)

        return df

    def _prepare_education(self, edu_df: pd.DataFrame) -> pd.DataFrame:
        if edu_df.empty:
            return pd.DataFrame()

        df = edu_df.copy()
        df['end_date'] = pd.to_datetime(df['end_date'], format='%Y-%m-%d', errors='coerce')
        df['start_date'] = pd.to_datetime(df['start_date'], format='%Y-%m-%d', errors='coerce')

        def get_most_recent(group):
            sorted_group = group.sort_values(
                by=['start_date', 'end_date'],
                ascending=[False, True]
            )
            return sorted_group.iloc[0:1]

        df_recent = df.groupby("id").apply(get_most_recent).droplevel(0)

        df_recent['academic_role'] = ""
        for member_id, row in df_recent.iterrows():
            if row['institution'] == INSTITUTION_FILTER:
                if row['degree'] == "Bachelors":
                    df_recent.at[member_id, 'academic_role'] = "Undergraduate Student"
                elif row['degree'] in ["PhD", "Masters"]:
                    df_recent.at[member_id, 'academic_role'] = "Graduate Student"

        return df_recent.add_suffix('_edu')

    def _merge_education_experience(
        self,
        exp_df: pd.DataFrame,
        edu_df: pd.DataFrame
    ) -> pd.DataFrame:
        if exp_df.empty and edu_df.empty:
            return pd.DataFrame()

        if exp_df.empty:
            return edu_df

        if edu_df.empty:
            return exp_df.add_suffix('_exp')

        def get_most_recent_exp(group):
            sorted_group = group.sort_values(
                by=['start_date', 'end_date'],
                ascending=[False, True]
            )
            relevant = sorted_group[
                sorted_group['group'].str.contains('|'.join(GROUP_FILTER), na=False)
            ]

            if len(relevant) > 0:
                return relevant.iloc[0:1]
            return sorted_group.iloc[0:1]

        exp_recent = exp_df.groupby("id").apply(get_most_recent_exp).droplevel(0)
        exp_recent = exp_recent.add_suffix('_exp')

        merged = exp_recent.merge(edu_df, on='id', how='outer')

        return merged

    def _determine_current_status(self, merged_df: pd.DataFrame) -> pd.DataFrame:
        if merged_df.empty:
            return pd.DataFrame()

        df = merged_df.copy()
        df['isCurrent'] = False
        df['current_role'] = ""

        now = datetime.now()

        for member_id, row in df.iterrows():
            institution_edu = row.get('institution_edu', '')
            end_date_edu = row.get('end_date_edu', pd.NaT)
            academic_role = row.get('academic_role_edu', '')

            group_exp = row.get('group_exp', '')
            end_date_exp = row.get('end_date_exp', pd.NaT)
            role_exp = row.get('role_exp', '')

            if institution_edu == INSTITUTION_FILTER:
                if pd.isna(end_date_edu) or end_date_edu >= now:
                    df.at[member_id, 'isCurrent'] = True
                    if pd.notna(end_date_exp):
                        df.at[member_id, 'isCurrent'] = False
                    if academic_role:
                        df.at[member_id, 'current_role'] = academic_role
                else:
                    df.at[member_id, 'isCurrent'] = False
                    if academic_role:
                        df.at[member_id, 'current_role'] = academic_role
                    else:
                        df.at[member_id, 'current_role'] = role_exp

            elif group_exp in GROUP_FILTER:
                if pd.isna(end_date_exp) or end_date_exp >= now:
                    df.at[member_id, 'isCurrent'] = True
                    df.at[member_id, 'current_role'] = role_exp
                else:
                    df.at[member_id, 'isCurrent'] = False
                    if academic_role:
                        df.at[member_id, 'current_role'] = academic_role
                    else:
                        df.at[member_id, 'current_role'] = role_exp

            else:
                df.at[member_id, 'isCurrent'] = False
                if academic_role:
                    df.at[member_id, 'current_role'] = academic_role
                else:
                    df.at[member_id, 'current_role'] = role_exp

            df.at[member_id, 'current_role'] = ROLE_MAP.get(
                df.at[member_id, 'current_role'],
                df.at[member_id, 'current_role']
            )

        return df

    def _add_member_info(
        self,
        current_df: pd.DataFrame,
        info_df: pd.DataFrame,
        projects_df: pd.DataFrame
    ) -> pd.DataFrame:
        if current_df.empty:
            return pd.DataFrame()

        current_with_role = current_df[["current_role"]]
        merged = pd.merge(current_with_role, info_df, on='id', how='inner')

        merged["current_project_title"] = ""
        for member_id in merged.index:
            if member_id in projects_df.index:
                member_projects = projects_df.loc[member_id]
                if not member_projects.empty:
                    if isinstance(member_projects, pd.Series):
                        project_title = member_projects["project_title"]
                    else:
                        project_title = member_projects.iloc[0]["project_title"]
                    merged.loc[member_id, "current_project_title"] = project_title

        merged.fillna("", inplace=True)

        return merged

    def _add_alumni_info(
        self,
        alumni_df: pd.DataFrame,
        info_df: pd.DataFrame
    ) -> pd.DataFrame:
        if alumni_df.empty:
            return pd.DataFrame()

        alumni_with_role = alumni_df[["current_role"]]
        merged = pd.merge(alumni_with_role, info_df, on='id', how='inner')
        merged = merged[['current_role', 'full_name']]

        return merged

    def sort_by_role_hierarchy(
        self,
        df: pd.DataFrame,
        role_hierarchy: Dict[str, int]
    ) -> pd.DataFrame:
        if df.empty:
            return df

        df_copy = df.copy()
        df_copy['rank'] = df_copy['current_role'].map(role_hierarchy)

        missing_roles = df_copy[df_copy['rank'].isna()]['current_role'].unique()
        if len(missing_roles) > 0:
            self.logger.warning(
                f"Roles not in hierarchy (will be sorted last): "
                f"{', '.join(missing_roles)}"
            )
            df_copy['rank'].fillna(999, inplace=True)

        df_sorted = df_copy.sort_values(by='rank')
        df_sorted.drop(columns='rank', inplace=True)

        return df_sorted

    def group_dataframe_by_id(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        if df.empty:
            return {}

        df_filled = df.fillna("")
        grouped = (
            df_filled.groupby("id")
            .apply(lambda x: x.to_dict(orient="records"))
            .reset_index(name="info")
            .set_index("id")
            .to_dict(orient="index")
        )

        return grouped
