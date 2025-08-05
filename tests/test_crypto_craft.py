import pytest
from app.email_bot import EmailToTelegramBot

# Helper to initialize the bot
bot = EmailToTelegramBot('user', 'pass', 'token', 'chat_id')

# Fixture for HTML Content
@pytest.fixture
def html_content_typical():
    return """
    <html>
        <img src='cc-impact-sm-red.png'>
        <div>Breaking: Major Update</div>
        <a href='http://example.com'>View Story</a>
    </html>
    """

@pytest.fixture
def html_content_edge():
    return """
    <html>
        <img src='cc-impact-sm-yel.png'>
        <style>body {font-family: 'Arial';}</style>
        <script>alert('Hello');</script>
        <div>Breaking: Edge Case Scenario</div>
        <span>View Story</span>
    </html>
    """

@pytest.fixture
def html_content_malformed():
    return """
    <html>
        <img src='cc-impact-sm-ora.png'>
        <div>Breaking</div>
    </malformed>
    """

# Test get_impact_emoji function
def test_get_impact_emoji_typical(html_content_typical):
    assert bot.get_impact_emoji(html_content_typical) == '🔴'

# Test parse_crypto_craft_email function
def test_parse_crypto_craft_email_typical(html_content_typical):
    result = bot.parse_crypto_craft_email(html_content_typical)
    assert "🔴 Breaking: Major Update" in result
    assert "[Read more](http://example.com)" in result

# Test edge cases
def test_get_impact_emoji_edge(html_content_edge):
    assert bot.get_impact_emoji(html_content_edge) == '🟡'

def test_parse_crypto_craft_email_edge(html_content_edge):
    result = bot.parse_crypto_craft_email(html_content_edge)
    assert "🟡 Breaking: Edge Case Scenario" in result
    # Note: View Story link extraction might not work with span instead of anchor tag

# Test malformed HTML
def test_get_impact_emoji_malformed(html_content_malformed):
    assert bot.get_impact_emoji(html_content_malformed) == '🟠'

def test_parse_crypto_craft_email_malformed(html_content_malformed):
    result = bot.parse_crypto_craft_email(html_content_malformed)
    # Should fall back to fallback message when parsing fails
    assert "🟠" in result
    assert "CryptoCraft Alert" in result or "Breaking" in result
