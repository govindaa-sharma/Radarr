import difflib

def compute_diff(old_text, new_text):
    if old_text is None:
        return {
            "has_change": True,
            "change_type": "new_page",
            "diff_summary": "First time scraping this page. Full content captured.",
            "added_lines": new_text.split(". "),
            "removed_lines": [],
            "similarity_score": 0.0
        }

    old_lines = [line.strip() for line in old_text.split(".") if line.strip()]
    new_lines = [line.strip() for line in new_text.split(".") if line.strip()]

    similarity = difflib.SequenceMatcher(None, old_text, new_text).ratio()

    differ = difflib.Differ()
    diff = list(differ.compare(old_lines, new_lines))

    added_lines = [line[2:] for line in diff if line.startswith("+ ")]
    removed_lines = [line[2:] for line in diff if line.startswith("- ")]

    has_change = len(added_lines) > 0 or len(removed_lines) > 0

    if not has_change:
        change_type = "no_change"
    elif similarity < 0.5:
        change_type = "major_change"
    elif similarity < 0.85:
        change_type = "moderate_change"
    else:
        change_type = "minor_change"

    diff_summary = build_diff_summary(added_lines, removed_lines, change_type)

    return {
        "has_change": has_change,
        "change_type": change_type,
        "diff_summary": diff_summary,
        "added_lines": added_lines[:20],
        "removed_lines": removed_lines[:20],
        "similarity_score": round(similarity, 3)
    }

def build_diff_summary(added_lines, removed_lines, change_type):
    if change_type == "no_change":
        return "No changes detected since last scrape."

    parts = []

    if removed_lines:
        parts.append(f"REMOVED ({len(removed_lines)} sections): " +
                     " | ".join(removed_lines[:3]))

    if added_lines:
        parts.append(f"ADDED ({len(added_lines)} sections): " +
                     " | ".join(added_lines[:3]))

    return " || ".join(parts)

def format_diff_for_analyst(diff_result, competitor, url, page_type):
    if not diff_result["has_change"]:
        return None

    return f"""
COMPETITOR: {competitor}
PAGE TYPE: {page_type}
URL: {url}
CHANGE TYPE: {diff_result["change_type"]}
SIMILARITY SCORE: {diff_result["similarity_score"]} (1.0 = identical, 0.0 = completely different)

WHAT WAS REMOVED:
{chr(10).join(diff_result["removed_lines"][:10]) if diff_result["removed_lines"] else "Nothing removed"}

WHAT WAS ADDED:
{chr(10).join(diff_result["added_lines"][:10]) if diff_result["added_lines"] else "Nothing added"}

SUMMARY: {diff_result["diff_summary"]}
""".strip()