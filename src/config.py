from pathlib import Path
from typing import List, Dict

BASE_DIR = Path(__file__).parent.parent
GROUP_DATA_DIR = BASE_DIR.parent / "group-data"
TEMPLATE_DIR_PATH = BASE_DIR / "templates"
WEBSITE_DATA_PATH = GROUP_DATA_DIR / "website_data"
HOSTING_PATH = BASE_DIR.parent / "kerzendorf-lab.github.io"
ARTICLE_DIR_PATH = BASE_DIR.parent / "research_news" / "articles"
ARTICLE_IMAGE_DESTINATION_DIR = HOSTING_PATH / "website_files" / "images" / "article_content"
MEMBERS_DIR_PATH = GROUP_DATA_DIR / "members"
SUB_RESEARCH_PATH = HOSTING_PATH / "sub_research"
OPPORTUNITIES_PATH = WEBSITE_DATA_PATH / "content" / "opportunities.json"
ROLE_HIERARCHY_PATH = WEBSITE_DATA_PATH / "role_hierarchy.json"
GALLERY_CONTENT_SOURCE = WEBSITE_DATA_PATH / "content" / "gallery"

GENERAL_TAGS: List[str] = [
    "Paper", "Poster", "Talk", "Award", "New Team Member",
    "PhD", "Conference", "Undergraduate", "Event", "Achievement"
]

TAG_COLORS: Dict[str, str] = {
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

ARTICLE_METADATA_FIELDS: List[str] = [
    "article_id", "category", "date", "tags",
    "title", "cover_image", "short_description"
]

GROUP_FILTER: List[str] = ["DTI", "TARDIS", "ICER", "kerzendorf"]
INSTITUTION_FILTER: str = "Michigan State University"

ROLE_MAP: Dict[str, str] = {
    "Assistant Professor": "Professor",
    "Professorial Assistant": "Undergraduate Student",
    "Visiting Researcher": "Postdoctoral Researcher"
}

DEGREE_MAP: Dict[str, str] = {
    "Masters": "Graduate Student",
    "PhD": "Postdoctorate",
    "Bachelors": "Undergraduate Student",
}

INDIVIDUAL_MEMBER_SECTION_MAP: Dict[str, str] = {
    "education": "Education",
    "experiences": "Experience",
    "projects": "Projects",
    "awards": "Awards & Recognition",
    "outreach": "Outreach Programs",
}
