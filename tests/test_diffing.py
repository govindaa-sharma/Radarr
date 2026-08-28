from tools.diffing import compute_diff
from tools.diffing import format_diff_for_analyst


def test_first_scrape_is_always_a_change():
    result = compute_diff(None, "Some brand new page content.")
    assert result["has_change"] is True
    assert result["change_type"] == "new_page"
    assert result["similarity_score"] == 0.0


def test_identical_text_has_no_change():
    text = "Our pricing is $10 per month for the Pro plan."
    result = compute_diff(text, text)
    assert result["has_change"] is False
    assert result["change_type"] == "no_change"
    assert result["similarity_score"] == 1.0


def test_minor_wording_change_is_classified_correctly():
    old = "Our pricing is $10 per month for the Pro plan. Contact sales for enterprise."
    new = "Our pricing is $10 per month for the Pro plan. Contact us for enterprise."
    result = compute_diff(old, new)
    assert result["has_change"] is True
    assert result["change_type"] in ("minor_change", "moderate_change")


def test_major_rewrite_is_classified_as_major_change():
    old = "Our pricing is $10 per month for the Pro plan."
    new = "We just raised a Series B and are hiring 40 engineers across three offices."
    result = compute_diff(old, new)
    assert result["has_change"] is True
    assert result["change_type"] == "major_change"
    assert result["similarity_score"] < 0.5


def test_added_and_removed_lines_are_captured():
    old = "Plan A costs 5 dollars. Plan B costs 10 dollars."
    new = "Plan A costs 5 dollars. Plan C costs 15 dollars."
    result = compute_diff(old, new)
    assert any("Plan C" in line for line in result["added_lines"])
    assert any("Plan B" in line for line in result["removed_lines"])


def test_no_change_does_not_generate_an_analyst_prompt():
    result = compute_diff("Unchanged page.", "Unchanged page.")
    assert format_diff_for_analyst(result, "Example", "https://example.com", "pricing") is None
