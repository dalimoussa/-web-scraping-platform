"""
Pytest configuration and fixtures.
"""

import pytest
from pathlib import Path


@pytest.fixture
def sample_html_official():
    """Sample official website HTML."""
    return """
    <html>
    <head>
        <title>田中太郎 Official Website</title>
    </head>
    <body>
        <h1>田中太郎</h1>
        <div class="profile">
            <p>年齢：45歳</p>
            <p>所属：自民党</p>
            <p>衆議院議員（東京都）</p>
        </div>
        <div class="sns">
            <a href="https://x.com/tanaka_taro">Twitter</a>
            <a href="https://www.instagram.com/tanaka_official/">Instagram</a>
        </div>
        <div class="policy">
            <h2>公約</h2>
            <p>地域活性化を推進します。教育改革に取り組みます。</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_election():
    """Sample election schedule HTML."""
    return """
    <html>
    <body>
        <h1>選挙予定</h1>
        <table>
            <tr>
                <th>選挙名</th>
                <th>実施日</th>
            </tr>
            <tr>
                <td>東京都知事選挙</td>
                <td>2024年12月15日</td>
            </tr>
            <tr>
                <td>参議院議員選挙</td>
                <td>2025年7月20日</td>
            </tr>
        </table>
    </body>
    </html>
    """


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir
