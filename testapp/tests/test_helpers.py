import io
import os
from unittest.mock import patch
from weasyprint import CSS

import pytest
from django.template.exceptions import TemplateDoesNotExist
from testapp.settings import TEMPLATE_CSS

from django_renderpdf import helpers
from django_renderpdf.helpers import InvalidRelativeUrl


TEMPLATE_CSS = [
    CSS(os.path.join('static','styles.css')),
]

def test_static_relative_fetched():
    fetched = helpers.django_url_fetcher("/static/styles.css")
    assert fetched == {
        "string": b"html { margin: 0; }\n",
        "mime_type": "text/css",
    }


def test_static_relative_not_found():
    with pytest.raises(InvalidRelativeUrl):
        helpers.django_url_fetcher("/static/non-existent.css")


def test_relative_staticfile_fetched():
    # Manifest files normally won't be found by a finder, but will be present in the
    # staticfiles storage.
    #
    # Patch `find()` to simulate exactly that:
    with patch(
        "django.contrib.staticfiles.finders.find",
        return_value=None,
        spec=True,
    ):
        fetched = helpers.django_url_fetcher("/static/styles.css")
        assert fetched == {
            "string": b"html { margin: 0; }\n",
            "mime_type": "text/css",
        }


def test_relative_url_resolves():
    fetched = helpers.django_url_fetcher("/view.css")
    assert fetched == {
        "string": b"* { background-color: red; }",
        "mime_type": "text/css",
    }


def test_bogus_relative_url_raises():
    with pytest.raises(InvalidRelativeUrl):
        helpers.django_url_fetcher("/non-existant.css")


def test_absolute_path_resolves():
    mocked_file = {"mime_type": "text/css", "string": "* { font-size: 100px; }"}

    with patch(
        "django_renderpdf.helpers.default_url_fetcher",
        return_value=mocked_file,
        spec=True,
    ) as default_fetcher:
        fetched = helpers.django_url_fetcher("https://example.com/style.css")

    assert default_fetcher.call_count == 1
    assert fetched == {"mime_type": "text/css", "string": "* { font-size: 100px; }"}


def test_render_pdf_single_template():
    file_ = io.BytesIO()
    helpers.render_pdf("test_template.html", file_, styles=TEMPLATE_CSS)

    # TODO: make sure some of the text from the template is actually in the PDF?
    #       this would benefit from some manual validation mechanism.
    data = file_.getvalue()
    assert data.startswith(b"%PDF-1.7\n")
    assert len(data) > 2000


def test_render_pdf_several_templates():
    file_ = io.BytesIO()
    helpers.render_pdf(
        ["test_template.html", "test_template_with_staticfile.html"],
        file_,
        styles=TEMPLATE_CSS
    )

    assert len(file_.getvalue()) > 2000


def test_render_pdf_with_some_non_existant():
    file_ = io.BytesIO()
    helpers.render_pdf(["idontexist.html", "test_template.html"], file_,
    styles=TEMPLATE_CSS)

    # Pdf for this template should be about 8kB
    assert len(file_.getvalue()) > 2000


def test_render_pdf_with_non_existant():
    file_ = io.BytesIO()

    with pytest.raises(TemplateDoesNotExist):
        helpers.render_pdf(["idontexist.html"], file_, styles=TEMPLATE_CSS)
