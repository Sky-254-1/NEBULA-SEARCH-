"""Test that _parse_html handles malformed/nested HTML correctly.

Regression test for CodeQL alert #24 — regex-based HTML stripping was
bypassable via nested tags like <scr<script>ipt>.
"""

import pytest
import tempfile
import os
from pathlib import Path

from app.search.ingestion import DocumentIngester


@pytest.fixture
def ingester():
    return DocumentIngester()


async def test_parse_html_nested_script_tag(ingester):
    """Nested script tag bypass: <scr<script>ipt> should not produce executable HTML.

    The key security property: no <script> tags or HTML markup should survive
    in the output — only plain text. Even with malformed nested tags, the
    parser must not produce executable content.
    """
    html = '<scr<script>ipt>alert("xss")</script>ipt>'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html)
        f.flush()
        path = Path(f.name)
    try:
        result = await ingester._parse_html(path)
        # No executable script tags should survive in the output
        assert '<script' not in result.lower()
        # The output should be plain text, not HTML markup
        assert '</script' not in result.lower()
        # Verify no executable content patterns survive
        assert '<scr' not in result.lower() or 'ipt>' not in result.lower()
    finally:
        os.unlink(path)


async def test_parse_html_normal_content(ingester):
    """Normal HTML content should be extracted correctly."""
    html = '<html><body><h1>Title</h1><p>Hello world</p></body></html>'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html)
        f.flush()
        path = Path(f.name)
    try:
        result = await ingester._parse_html(path)
        assert 'Title' in result
        assert 'Hello world' in result
    finally:
        os.unlink(path)


async def test_parse_html_script_style_removed(ingester):
    """Script and style content should be removed entirely."""
    html = '<style>body{color:red}</style><script>var x=1</script><p>Content</p>'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html)
        f.flush()
        path = Path(f.name)
    try:
        result = await ingester._parse_html(path)
        assert 'Content' in result
        assert 'color:red' not in result
        assert 'var x=1' not in result
    finally:
        os.unlink(path)


async def test_parse_html_attribute_with_gt(ingester):
    """Attribute containing > should not break parsing."""
    html = '<div title="a > b">Text content</div>'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html)
        f.flush()
        path = Path(f.name)
    try:
        result = await ingester._parse_html(path)
        assert 'Text content' in result
    finally:
        os.unlink(path)