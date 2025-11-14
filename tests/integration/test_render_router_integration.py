"""Integration coverage for render router decision logic."""

import pytest

from webarc.config.loader import load_config
from webarc.render.router import RenderRouter


@pytest.fixture
def router():
    config = load_config()
    return RenderRouter(config)


def test_render_router_static_content(router):
    html = "<html><body><h1>Title</h1><p>" + "text " * 300 + "</p></body></html>"
    assert router.check_js_needed(html, "https://example.com/page") is False


def test_render_router_low_content(router):
    html = "<html><body><p>Short</p></body></html>"
    assert router.check_js_needed(html, "https://example.com/page") is True


def test_render_router_force_js():
    config = load_config()
    config.render.force_js = True
    router = RenderRouter(config)
    assert router.check_js_needed("<html></html>", "https://example.com") is True


def test_render_router_mark_domain(router):
    router.mark_domain_js_needed("https://example.com/page")
    html = "<html><body><p>Content</p></body></html>"
    assert router.check_js_needed(html, "https://example.com/other") is True

