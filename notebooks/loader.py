# Imports
import json
import pandas as pd
from pathlib import Path
import shutil
from jinja2 import Environment, FileSystemLoader

# Path Configuration
GROUP_DATA_DIR = Path("/Users/atharva/workspace/code/tardis-main/lab/group-data")
MEMBERS_DIR_PATH = GROUP_DATA_DIR / "members/"
ARTICLE_DIR_PATH = Path("/Users/atharva/workspace/code/tardis-main/website/research_news/articles")
HOSTING_PATH = Path("/Users/atharva/workspace/code/tardis-main/lab/kerzendorf-lab.github.io")
ARTICLE_IMAGE_DESTINATION_DIR = HOSTING_PATH / "website_files" / "images" / "article_content"
TEMPLATE_DIR_PATH = GROUP_DATA_DIR.parent / "groupwebsite_generator" / "templates"
WEBSITE_DATA_PATH = GROUP_DATA_DIR / "website_data/"
ROLE_HIERARCHY_PATH = WEBSITE_DATA_PATH / "role_hierarchy.json"

# Data Mapping Constants
ROLE_MAP = {
    "Assistant Professor": "Professor",
    "Professorial Assistant": "Undergraduate Student",
    "Visiting Researcher": "Postdoctoral Researcher"
}

DEGREE_MAP = {
    "Masters": "Graduate Student",
    "PhD": "Postdoctorate",
    "Bachelors": "Undergraduate Student",
}

INDIVIDUAL_MEMBER_SECTION_MAP = {
    "education": "Education",
    "experiences": "Experience",
    "projects": "Projects",
    "awards": "Awards & Recognition",
    "outreach": "Outreach Programs",
}

# Filtering Constants
GROUP_FILTER = ["DTI", "TARDIS", "ICER", "kerzendorf"]
INSTITUTION_FILTER = "Michigan State University"

# Tag Colors for Articles
TAG_COLORS = {
    'paper': '#FF6B6B',
    'poster': '#4ECDC4',
    'talk': '#45B7D1',
    'award': '#96CEB4',
    'new team member': '#FFBE0B',
    'phd': '#9B5DE5',
    'conference': '#FF006E',
    'undergraduate': '#8338EC',
    'event': '#3A86FF',
    'achievement': '#FB5607',
    'astrophysics': '#2EC4B6',
    'machine learning': '#FF9F1C',
    'software': '#E71D36',
    'research': '#011627',
    'news': '#41EAD4'
}

# Helper Functions
def page_link(a):
    """Return the HTML file name after replacing blank spaces with underscores"""
    return a.replace(" ", "_") if " " in a else a

def group_df(df):
    """Group dataframe by index and convert to nested dict format for templates"""
    return df.fillna("").groupby(level=0).apply(lambda x: x.to_dict('records')).to_frame('info').to_dict('index')

def create_page(template, html, **kwargs):
    """Create an HTML page using a Jinja2 template and save it to a specified path"""
    page_template = environment.get_template(template)
    template_level = html.count("/")
    page_html_path = HOSTING_PATH / html
    page_html_path.parent.mkdir(parents=True, exist_ok=True)
    page_content = page_template.render(TEMPLATE_LEVEL=template_level, **kwargs)
    with open(page_html_path, mode="w", encoding="utf-8") as page:
        page.write(page_content)

# Setup Jinja2 environment
environment = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR_PATH), extensions=["jinja2.ext.loopcontrols", "jinja2.ext.do"]
)
environment.globals["page_link"] = page_link


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
                if field in record and record[field]:
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
        single_date_with_errors = ['awards.json', 'publications.json']

        members_data = []

        for member_dir in self.members_dir.glob("*"):
            if not member_dir.is_dir():
                continue

            info_path = member_dir / "info.json"
            if not info_path.exists():
                continue

            member_info = json.loads(info_path.read_text())
            if 'id' not in member_info:
                continue
            member_id = member_info["id"]

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
                data[key].extend(records)

        members_df = pd.DataFrame(members_data).set_index('id')
        members_df.index.name = 'member_id'
        self.members_df = members_df

        for key in data:
            df = pd.DataFrame(data[key]).set_index('member_id')
            setattr(self, f"{key}_df", df)


class ArticleDataLoader:
    def __init__(self, article_dir: Path, image_dest_dir: Path):
        self.article_dir = article_dir
        self.image_dest_dir = image_dest_dir

    def _copy_image(self, source_dir, image_path_str):
        """Copy image from article media to destination, return new path"""
        # Skip URLs
        if image_path_str.startswith(('http://', 'https://')):
            return image_path_str

        image_name = Path(image_path_str).name
        source = source_dir.parent / "media" / "images" / image_name
        dest = self.image_dest_dir / image_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        return f"website_files/images/article_content/{image_name}"

    def _process_images(self, article, source_dir):
        """Process all images in article (cover + content)"""
        if article.get("cover_image"):
            article["cover_image"] = self._copy_image(source_dir, article["cover_image"])

        # Process all image keys in content
        if "content" in article:
            for key, val in article["content"].items():
                if "img" in key and val:
                    article["content"][key] = self._copy_image(source_dir, val)

    def load_all_articles(self):
        """Load all articles without filtering"""
        articles = []
        for info_json in self.article_dir.rglob('info.json'):
            article = json.loads(info_json.read_text())
            self._process_images(article, info_json)
            articles.append(article)

        self.articles_df = pd.DataFrame(articles).set_index('article_id')
        self.articles_df["date"] = pd.to_datetime(self.articles_df["date"], format="%m-%d-%Y")


loader = MemberDataLoader()
loader.load_all_data()

print(f"Members: {len(loader.members_df)}")
print(f"Education records: {len(loader.education_df)}")
print(f"Experiences records: {len(loader.experiences_df)}")
print(f"Projects records: {len(loader.projects_df)}")
print(f"Awards records: {len(loader.awards_df)}")
print(f"Outreach records: {len(loader.outreach_df)}")
print(f"Documents records: {len(loader.documents_df)}")
print(f"Posters records: {len(loader.posters_df)}")
print(f"Publications records: {len(loader.publications_df)}")

# Fix index name to 'id' for template compatibility
loader.members_df = loader.members_df.rename_axis('id')

# Create grouped dicts with 'info' key for template
education = group_df(loader.education_df)
experience = group_df(loader.experiences_df)
projects = group_df(loader.projects_df)
awards = group_df(loader.awards_df)
outreach = group_df(loader.outreach_df)

# Extract socials to separate dict
social_cols = ['website', 'github_handle', 'twitter_handle', 'linkedin_handle', 'email', 'orcid']
socials = loader.members_df[social_cols].fillna('').to_dict('index')

# Load articles
article_loader = ArticleDataLoader(ARTICLE_DIR_PATH, ARTICLE_IMAGE_DESTINATION_DIR)
article_loader.load_all_articles()
print(f"Articles: {len(article_loader.articles_df)}")

# Load general website data
general = json.loads((WEBSITE_DATA_PATH / "general.json").read_text())

# Create grouped dict for documents
documents = group_df(loader.documents_df) if not loader.documents_df.empty else {}

# Create individual member pages
for person_id, person_data in loader.members_df.iterrows():
    create_page(
        "individual_person.html.j2",
        f"members/{person_id}/{person_id}.html",
        general=general,
        member_id=person_id,
        member_data=person_data,
        socials=socials,
        documents=documents,
        education=education,
        experience=experience,
        projects=projects,
        awards=awards,
        outreach=outreach,
        section_headings=INDIVIDUAL_MEMBER_SECTION_MAP,
        content=article_loader.articles_df.to_dict("index"),
    )

print(f"Created {len(loader.members_df)} individual member pages")