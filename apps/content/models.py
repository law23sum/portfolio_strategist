from django.db import models
from modelcluster.fields import ParentalKey
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Orderable, Page
from wagtail.search import index

from apps.content.blocks import CaptionBlock


def _get_default_block_types():
    return [
        ("paragraph", blocks.RichTextBlock()),
        ("image", ImageChooserBlock()),
        ("caption", CaptionBlock()),
        ("html", blocks.RawHTMLBlock()),
    ]


class BaseContentPage(Page):
    social_image = models.ImageField(null=True, blank=True, help_text="The image to use in social sharing metadata.")
    promote_panels = Page.promote_panels + [
        FieldPanel("social_image"),
    ]

    def get_social_image_url(self):
        if self.social_image:
            return self.social_image.url
        return ""

    class Meta:
        abstract = True


class ContentPage(BaseContentPage):
    """
    A page of generic content.
    """

    body = StreamField(_get_default_block_types())
    content_panels = Page.content_panels + [
        FieldPanel("body", classname="full"),
    ]


class BlogIndexPage(BaseContentPage):
    """
    Index page for a blog
    """

    intro = RichTextField(blank=True)
    content_panels = Page.content_panels + [FieldPanel("intro", classname="full")]

    def get_ordered_blog_posts(self):
        return self.get_children().live().order_by("-first_published_at")


class BlogPage(BaseContentPage):
    """
    A single blog post
    """

    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = StreamField(_get_default_block_types())

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        InlinePanel("gallery_images", label="Gallery images"),
    ]

    @property
    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None


class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ForeignKey("wagtailimages.Image", on_delete=models.CASCADE, related_name="+")
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        FieldPanel("image"),
        FieldPanel("caption"),
    ]
