import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from abc import ABC, abstractmethod

from src.config import TEMPLATE_DIR_PATH, HOSTING_PATH, TAG_COLORS
from src.utils.path_helpers import page_link, get_tag_color

class BasePageRenderer(ABC):
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.hosting_path = HOSTING_PATH
        self.environment = self._setup_jinja_environment()

    def _setup_jinja_environment(self) -> Environment:
        env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR_PATH),
            extensions=["jinja2.ext.loopcontrols", "jinja2.ext.do"]
        )

        env.globals["page_link"] = page_link
        env.globals['tag_colors'] = TAG_COLORS
        env.globals['get_tag_color'] = lambda tag: get_tag_color(tag, TAG_COLORS)

        return env

    def render_page(
        self,
        template_name: str,
        output_path: str,
        **context
    ) -> None:
        try:
            template = self.environment.get_template(template_name)
        except Exception as e:
            raise ValueError(
                f"Failed to load template '{template_name}'. "
                f"Check that file exists in {TEMPLATE_DIR_PATH}. "
                f"Error: {e}"
            ) from e

        template_level = output_path.count("/")

        full_output_path = self.hosting_path / output_path
        full_output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            content = template.render(TEMPLATE_LEVEL=template_level, **context)
        except Exception as e:
            raise ValueError(
                f"Failed to render template '{template_name}' for '{output_path}'. "
                f"Check template syntax and context variables. "
                f"Error: {e}"
            ) from e

        try:
            with open(full_output_path, mode="w", encoding="utf-8") as f:
                f.write(content)

            self.logger.debug(f"Rendered: {output_path}")
        except IOError as e:
            raise IOError(
                f"Failed to write output file '{full_output_path}'. "
                f"Check disk space and permissions. "
                f"Error: {e}"
            ) from e

    @abstractmethod
    def render(self, **kwargs) -> None:
        pass
