import json
import pandas as pd
from pathlib import Path
import shutil
import re
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
ARTICLE_DIR_PATH = (CONFIG_DIR / config["paths"]["article_dir"]).resolve()
HOSTING_PATH = (CONFIG_DIR / config["paths"]["hosting_path"]).resolve()
ARTICLE_IMAGE_DESTINATION_DIR = HOSTING_PATH / "website_files" / "images" / "article_content"

DEFAULT_COVER_IMAGE_HEIGHT = config.get("default_cover_image_height", "330px")
DEFAULT_COVER_IMAGE_WIDTH = config.get("default_cover_image_width", "520px")


# Utility function
def urlize_content(content_text, members_df, current_members_df):
    """Replace [member_id] with linked names"""
    def replace_id(match):
        id_to_fetch = match.group(1)
        if id_to_fetch in members_df.index:
            name = members_df.loc[id_to_fetch, 'full_name']
            if id_to_fetch in current_members_df.index:
                return f'<a href="../members/{id_to_fetch}/{id_to_fetch}.html" target="_blank">{name}</a>'
            return name
        return id_to_fetch.replace('_', ' ').title()

    return re.sub(r'\[(\w+)\]', replace_id, content_text)


class ArticleDataLoader:
    def __init__(self, article_dir: Path, image_dest_dir: Path, members_df: pd.DataFrame, current_members_df: pd.DataFrame, platform_filter: str = None, category_replacements: dict = None):
        self.article_dir = article_dir
        self.image_dest_dir = image_dest_dir
        self.members_df = members_df
        self.current_members_df = current_members_df
        self.platform_filter = platform_filter if platform_filter is not None else config.get("platform_filter", "kg")
        self.category_replacements = category_replacements if category_replacements is not None else config.get("category_replacements", {})

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
        if article["cover_image"]:
            article["cover_image"] = self._copy_image(source_dir, article["cover_image"])

        for key, val in article["content"].items():
            if "img" in key and val:
                article["content"][key] = self._copy_image(source_dir, val)

    def split_news_research(self):
        """Split articles into news and research dataframes"""
        is_news = (
            (self.articles_df["category"] == "News") |
            self.articles_df["tags"].apply(lambda x: "news" in x if isinstance(x, list) else False)
        )

        self.news_df = self.articles_df[is_news].sort_values("date", ascending=False)
        self.research_df = self.articles_df[~is_news].sort_values(["category", "date"], ascending=[True, False])

    def load_all_articles(self):
        """Load articles filtered by platform and date"""
        articles = []
        today = datetime.now()

        for info_json in self.article_dir.rglob('info.json'):
            article = json.loads(info_json.read_text())

            if self.platform_filter not in article["platforms"]:
                continue

            article_date = pd.to_datetime(article["date"], format="%m-%d-%Y")
            if article_date > today:
                continue

            article["date"] = article_date
            self._process_images(article, info_json)

            if article["category"] == "News" or ("news" in article["tags"]):
                for key, val in article["content"].items():
                    if "para" in key:
                        article["content"][key] = urlize_content(val, self.members_df, self.current_members_df)

            articles.append(article)

        if articles:
            self.articles_df = pd.DataFrame(articles).set_index('article_id')
            self.articles_df["cover_image_height"] = self.articles_df["cover_image_height"].fillna(DEFAULT_COVER_IMAGE_HEIGHT).replace("", DEFAULT_COVER_IMAGE_HEIGHT)
            self.articles_df["cover_image_width"] = self.articles_df["cover_image_width"].fillna(DEFAULT_COVER_IMAGE_WIDTH).replace("", DEFAULT_COVER_IMAGE_WIDTH)
            self.articles_df["category"] = self.articles_df["category"].replace(self.category_replacements)
            self.articles_df['image_name'] = self.articles_df['cover_image'].apply(lambda x: Path(x).name)
            self.split_news_research()
        else:
            self.articles_df = pd.DataFrame()
            self.news_df = pd.DataFrame()
            self.research_df = pd.DataFrame()


# Load member data from CSVs
members_df = pd.read_csv("members.csv", index_col=0)
current_members_df = pd.read_csv("current_members.csv", index_col=0)

print(f"Loaded {len(members_df)} members")
print(f"Loaded {len(current_members_df)} current members")

# Load articles
article_loader = ArticleDataLoader(
    ARTICLE_DIR_PATH,
    ARTICLE_IMAGE_DESTINATION_DIR,
    members_df,
    current_members_df
)
article_loader.load_all_articles()

print(f"Articles: {len(article_loader.articles_df)}")
print(f"News articles: {len(article_loader.news_df)}")
print(f"Research articles: {len(article_loader.research_df)}")

# Save to CSV
article_loader.articles_df.to_csv("articles.csv")
article_loader.news_df.to_csv("news.csv")
article_loader.research_df.to_csv("research.csv")

print(f"Saved articles.csv ({len(article_loader.articles_df)} articles)")
print(f"Saved news.csv ({len(article_loader.news_df)} news articles)")
print(f"Saved research.csv ({len(article_loader.research_df)} research articles)")
