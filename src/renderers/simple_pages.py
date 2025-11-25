from .base import BasePageRenderer

class HomepageRenderer(BasePageRenderer):
    def render(self, general, homepage, recent_content) -> None:
        self.logger.info("Rendering homepage")

        self.render_page(
            "homepage.html.j2",
            "index.html",
            general=general,
            homepage=homepage,
            recent_content=recent_content.to_dict(orient="records"),
        )

class ContactPageRenderer(BasePageRenderer):
    def render(self, general, contact) -> None:
        self.logger.info("Rendering contact page")

        self.render_page(
            "contact.html.j2",
            "Contact.html",
            general=general,
            contact=contact
        )

class SupportPageRenderer(BasePageRenderer):
    def render(self, general, support) -> None:
        self.logger.info("Rendering support page")

        self.render_page(
            "support.html.j2",
            "Support.html",
            general=general,
            support=support
        )

class JoinUsPageRenderer(BasePageRenderer):
    def render(self, general, opportunities) -> None:
        self.logger.info("Rendering join us page")

        self.render_page(
            "join_us.html.j2",
            "Join_Us.html",
            general=general,
            opportunities=opportunities
        )
