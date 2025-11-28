from pathlib import Path

def page_link(text: str) -> str:
    return text.replace(" ", "_") if " " in text else text

def get_tag_color(tag: str, tag_colors: dict) -> str:
    return tag_colors.get(tag.lower(), '#6c757d')

def set_new_image_path(source_dir: Path, old_image_path: Path, destination_dir: Path) -> str:
    article_image_path = source_dir.parent / "media" / "images"
    image_source = article_image_path / old_image_path.name
    image_destination = destination_dir / old_image_path.name

    if not image_source.exists():
        raise FileNotFoundError(
            f"Source image not found: {image_source}. "
            f"Expected in {article_image_path}. "
            f"Original path reference: {old_image_path}"
        )

    image_destination.parent.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy2(image_source, image_destination)

    website_files_index = image_destination.parts.index("website_files")
    new_image_path = Path(*image_destination.parts[website_files_index:])

    return str(new_image_path)
