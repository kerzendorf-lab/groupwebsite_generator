import ast
import json
import pandas as pd
from pathlib import Path
import shutil
from PIL import Image
from jinja2 import Environment, FileSystemLoader

# Configuration - Edit this to switch between websites
CONFIG_FILE = "config_dti.json"  # or "config_dti.json"

# CONFIG_FILE = "config_lab.json"
# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / CONFIG_FILE
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)
CONFIG_DIR = CONFIG_PATH.parent

# Constants - resolve paths relative to config directory
CSV_DIR_PATH = Path(".")
GROUP_DATA_DIR = (CONFIG_DIR / config["paths"]["group_data_dir"]).resolve()
HOSTING_PATH = (CONFIG_DIR / config["paths"]["hosting_path"]).resolve()
TEMPLATE_DIR_PATH = (CONFIG_DIR / config["paths"]["template_dir"]).resolve()
WEBSITE_DATA_PATH = GROUP_DATA_DIR / "website_data/"
GALLERY_CONTENT_SOURCE = WEBSITE_DATA_PATH / "content" / "gallery"
SOURCE_ASSETS = (CONFIG_DIR / config["paths"]["source_assets"]).resolve()
SUB_RESEARCH_PATH = HOSTING_PATH / "sub_research"
OPPORTUNITIES_PATH = WEBSITE_DATA_PATH / "content" / "opportunities.json"

TAG_COLORS = config.get("tag_colors", {})

# Utility functions

# Helper Functions
def page_link(a):
    """Return the HTML file name after replacing blank spaces with underscores"""
    return a.replace(" ", "_") if " " in a else a

def group_df(df):
    """Group dataframe by index and convert to nested dict format for templates"""
    return df.fillna("").groupby(level=0).apply(lambda x: x.to_dict('records')).to_frame('info').to_dict('index')

def get_tag_color(tag):
    """Get color for a specific tag, with fallback to default"""
    return TAG_COLORS.get(tag.lower(), '#6c757d')

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
environment.globals['tag_colors'] = TAG_COLORS
environment.globals['get_tag_color'] = get_tag_color

# Load member and article data from CSVs
members_df = pd.read_csv(CSV_DIR_PATH / "members.csv", index_col=0)
current_members_with_info = pd.read_csv(CSV_DIR_PATH / "current_members.csv", index_col=0)
# Replace NaN with empty string for current_project_title to avoid displaying "nan"
current_members_with_info['current_project_title'] = current_members_with_info['current_project_title'].fillna('')
alumni_members_with_info = pd.read_csv(CSV_DIR_PATH / "alumni_members.csv", index_col=0)
articles_df = pd.read_csv(CSV_DIR_PATH / "articles.csv", index_col=0)
news_df = pd.read_csv(CSV_DIR_PATH / "news.csv", index_col=0)
research_df = pd.read_csv(CSV_DIR_PATH / "research.csv", index_col=0)

# Parse dates if the column exists and has data
if not articles_df.empty and 'date' in articles_df.columns:
    articles_df['date'] = pd.to_datetime(articles_df['date'])
if not news_df.empty and 'date' in news_df.columns:
    news_df['date'] = pd.to_datetime(news_df['date'])
if not research_df.empty and 'date' in research_df.columns:
    research_df['date'] = pd.to_datetime(research_df['date'])

# Convert string columns back to their original types
for df in [articles_df, news_df, research_df]:
    if not df.empty and 'content' in df.columns:
        df['content'] = df['content'].apply(ast.literal_eval)
    if not df.empty and 'links' in df.columns:
        df['links'] = df['links'].apply(ast.literal_eval)
    if not df.empty and 'people_involved_ids' in df.columns:
        df['people_involved_ids'] = df['people_involved_ids'].apply(ast.literal_eval)
    if not df.empty and 'tags' in df.columns:
        df['tags'] = df['tags'].apply(ast.literal_eval)
    if not df.empty and 'platforms' in df.columns:
        df['platforms'] = df['platforms'].apply(ast.literal_eval)

# Get recent content for homepage
if not articles_df.empty and 'category' in articles_df.columns and 'date' in articles_df.columns:
    recent_content_df = articles_df.sort_values(
        ["category", "date"], ascending=[True, False]
    ).groupby("category").head(1)
else:
    recent_content_df = pd.DataFrame()

print(f"Loaded {len(members_df)} members from CSV")
print(f"Loaded {len(current_members_with_info)} current members from CSV")
print(f"Loaded {len(alumni_members_with_info)} alumni members from CSV")
print(f"Loaded {len(articles_df)} articles from CSV")

# Load individual member data from CSVs
education_df = pd.read_csv(CSV_DIR_PATH / "education.csv", index_col=0)
experiences_df = pd.read_csv(CSV_DIR_PATH / "experiences.csv", index_col=0)
projects_df = pd.read_csv(CSV_DIR_PATH / "projects.csv", index_col=0)
awards_df = pd.read_csv(CSV_DIR_PATH / "awards.csv", index_col=0)
outreach_df = pd.read_csv(CSV_DIR_PATH / "outreach.csv", index_col=0)
documents_df = pd.read_csv(CSV_DIR_PATH / "documents.csv", index_col=0)

# Parse dates for dataframes with date columns
for df in [education_df, experiences_df, projects_df, outreach_df]:
    if 'start_date' in df.columns:
        df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
    if 'end_date' in df.columns:
        df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')

# Awards has additional 'date' column
if 'date' in awards_df.columns:
    awards_df['date'] = pd.to_datetime(awards_df['date'], errors='coerce')
if 'start_date' in awards_df.columns:
    awards_df['start_date'] = pd.to_datetime(awards_df['start_date'], errors='coerce')
if 'end_date' in awards_df.columns:
    awards_df['end_date'] = pd.to_datetime(awards_df['end_date'], errors='coerce')

# Group dataframes
education = group_df(education_df)
experience = group_df(experiences_df)
projects = group_df(projects_df)
awards = group_df(awards_df)
outreach = group_df(outreach_df)

# Setup socials and dicts
# Load social fields from schema
social_schema_path = GROUP_DATA_DIR / "schemas/members/social_links.json"
if social_schema_path.exists():
    social_schema = json.loads(social_schema_path.read_text())
    social_cols = list(social_schema['properties'].keys())
    # Only get columns that exist in members_df
    existing_social_cols = [col for col in social_cols if col in members_df.columns]
    if existing_social_cols:
        socials = members_df[existing_social_cols].fillna('').to_dict('index')
    else:
        socials = {idx: {} for idx in members_df.index}
else:
    socials = {idx: {} for idx in members_df.index}

general = json.loads((WEBSITE_DATA_PATH / "general.json").read_text())


all_members_dict = members_df.to_dict("index")
all_articles_dict = {
    aid: {**data, 'article_id': aid}
    for aid, data in articles_df.to_dict("index").items()
}

# Create individual member pages
section_headings = config.get("individual_member_section_map", {})
for person_id, person_data in members_df.iterrows():
    create_page(
        "individual_person.html.j2",
        f"members/{person_id}/{person_id}.html",
        general=general,
        member_id=person_id,
        member_data=person_data,
        socials=socials,
        documents=documents_df,
        education=education,
        experience=experience,
        projects=projects,
        awards=awards,
        outreach=outreach,
        content=all_articles_dict,
        section_headings=section_headings,
    )

print(f"Created {len(members_df)} individual member pages")

# Gallery page- unused
# gallery_loader = GalleryDataLoader(GALLERY_CONTENT_SOURCE, HOSTING_PATH / "website_files" / "images" / "gallery")
# gallery_loader.load_all_events()

# create_page(
#     "gallery.html.j2",
#     "Gallery.html",
#     general=general,
#     member_data=all_members_dict,
#     events=gallery_loader.events
# )

# Copy assets and load JSON files
shutil.copytree(SOURCE_ASSETS, HOSTING_PATH / "assets", dirs_exist_ok=True)

homepage = json.loads((WEBSITE_DATA_PATH / "homepage.json").read_text())
contact = json.loads((WEBSITE_DATA_PATH / "contact.json").read_text())
support = json.loads((WEBSITE_DATA_PATH / "support.json").read_text())
research = json.loads((WEBSITE_DATA_PATH / "research_categories.json").read_text())

# Create homepage
create_page(
    "homepage.html.j2",
    "index.html",
    general=general,
    homepage=homepage,
    recent_content=recent_content_df.reset_index().to_dict(orient="records"),
)

# Create current members page
create_page(
    "current_members.html.j2",
    "current_members.html",
    general=general,
    current_members=current_members_with_info.to_dict('index'),
    socials=socials
)

# Create alumni page
create_page(
    "alumni_members.html.j2",
    "alumni_members.html",
    general=general,
    alumni_members=alumni_members_with_info,
)

# Create contact page
create_page(
    "contact.html.j2",
    "Contact.html",
    general=general,
    contact=contact
)

# Create support page
create_page(
    "support.html.j2",
    "Support.html",
    general=general,
    support=support
)

# Create research page
if not research_df.empty:
    research_template = config.get("templates", {}).get("research", "research.html.j2")
    research_page = config.get("pages", {}).get("research", "Research.html")
    create_page(
        research_template,
        research_page,
        general=general,
        content=research_df.reset_index(),
        research=research,
        current_members=all_members_dict,
    )

# Create sub_research directory
SUB_RESEARCH_PATH.mkdir(parents=True, exist_ok=True)

# Create category pages
if not research_df.empty:
    for category in research_df["category"].unique():
        create_page(
            "sub_research_frontpage.html.j2",
            f"sub_research/{page_link(category.lower())}.html",
            general=general,
            research=research,
            content=research_df.reset_index(),
            category=category,
            current_members=all_members_dict,
        )

    # Create individual research pages
    for article_id, ind_research_values in research_df.iterrows():
        destination_research_path = f"sub_research/{page_link(ind_research_values.category.lower())}/{page_link(article_id.lower())}.html"
        if ind_research_values['category'] == "Software":
            destination_research_path = f"sub_research/{page_link(article_id.lower())}.html"

        folder_path = SUB_RESEARCH_PATH / page_link(ind_research_values.category.lower())
        folder_path.mkdir(parents=True, exist_ok=True)
        create_page(
            "research_page_no_twitter.html.j2",
            destination_research_path,
            general=general,
            content=ind_research_values,
            member_data=all_members_dict,
            article_id=article_id,
        )

# Create news page
create_page(
    "news.html.j2",
    "News.html",
    general=general,
    content=news_df.reset_index(),
    category="News",
    member_data=all_members_dict,
)

# Create individual news pages
if not news_df.empty:
    news_dict_list = news_df.reset_index().to_dict('records')
    for news_item in news_dict_list:
        create_page(
            "news_page_no_twitter.html.j2",
            f"news/{page_link(news_item['article_id'].lower())}.html",
            general=general,
            content=news_item,
            member_data=all_members_dict,
            category="News"
        )

# Create join us page
join_us_template = TEMPLATE_DIR_PATH / "join_us.html.j2"
if OPPORTUNITIES_PATH.exists() and join_us_template.exists():
    with open(OPPORTUNITIES_PATH, 'r') as f_opp:
        opportunities = json.load(f_opp)

    create_page(
        "join_us.html.j2",
        "Join_Us.html",
        general=general,
        opportunities=opportunities
    )
