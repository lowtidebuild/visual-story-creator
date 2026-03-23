#!/usr/bin/env python3
"""
qa-check.py — Quality Assurance validator for generated story.html

Usage:
    python3 scripts/qa-check.py output/build/story.html          # human-readable + writes report
    python3 scripts/qa-check.py output/build/story.html --json   # JSON to stdout only

Exit codes:
    0 — all checks pass
    1 — one or more checks fail
"""

import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser


# ---------------------------------------------------------------------------
# HTML Parser
# ---------------------------------------------------------------------------


class StoryHTMLParser(HTMLParser):
    """Parse story HTML and collect data needed for QA checks."""

    def __init__(self):
        super().__init__()
        self.has_viewport_meta = False
        self.has_og_title = False
        self.has_og_description = False
        self.images: list[dict] = []  # list of {"alt": str|None, "loading": str|None}
        self.beat_sections: int = 0
        self.style_blocks: list[str] = []  # raw text from <style> tags
        self._in_style = False
        self._current_style = []

    def handle_starttag(self, tag: str, attrs: list[tuple]):
        attr_dict = dict(attrs)

        if tag == "meta":
            name = attr_dict.get("name", "").lower()
            prop = attr_dict.get("property", "").lower()
            content = attr_dict.get("content", "")

            # viewport
            if name == "viewport" and "width=device-width" in content:
                self.has_viewport_meta = True

            # OG tags
            if prop == "og:title":
                self.has_og_title = True
            if prop == "og:description":
                self.has_og_description = True

        elif tag == "img":
            alt = attr_dict.get("alt")  # None if attribute absent
            loading = attr_dict.get("loading")
            self.images.append({"alt": alt, "loading": loading})

        elif tag == "section":
            cls = attr_dict.get("class", "")
            if "beat-" in cls:
                self.beat_sections += 1

        elif tag == "style":
            self._in_style = True
            self._current_style = []

    def handle_endtag(self, tag: str):
        if tag == "style" and self._in_style:
            self.style_blocks.append("".join(self._current_style))
            self._in_style = False
            self._current_style = []

    def handle_data(self, data: str):
        if self._in_style:
            self._current_style.append(data)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_viewport_meta(parser: StoryHTMLParser) -> dict:
    passed = parser.has_viewport_meta
    return {
        "pass": passed,
        "detail": (
            'Found <meta name="viewport" content="width=device-width...">'
            if passed
            else "Missing viewport meta tag"
        ),
    }


def check_font_hierarchy(parser: StoryHTMLParser) -> dict:
    """At least 3 distinct font-size values in inline <style> blocks."""
    all_css = "\n".join(parser.style_blocks)
    # Match font-size values: numbers with px/rem/em/%, or named sizes
    raw_values = re.findall(
        r"font-size\s*:\s*([\d.]+(?:px|rem|em|%|vw|vh|pt)|small|medium|large|x-large|xx-large)",
        all_css,
        re.IGNORECASE,
    )
    distinct = set(v.lower() for v in raw_values)
    count = len(distinct)
    passed = count >= 3
    return {
        "pass": passed,
        "detail": (
            f"{count} distinct font-size values found (need \u22653)"
            if not passed
            else f"{count} distinct font-size values found"
        ),
        "values": sorted(distinct),
    }


def check_text_column_width(parser: StoryHTMLParser) -> dict:
    """max-width with 680px or var(--text-width) exists in <style> blocks."""
    all_css = "\n".join(parser.style_blocks)
    has_680 = bool(re.search(r"max-width\s*:\s*680px", all_css, re.IGNORECASE))
    has_var = bool(re.search(r"max-width\s*:\s*var\(--text-width\)", all_css, re.IGNORECASE))
    passed = has_680 or has_var
    if passed:
        detail = "max-width: 680px found" if has_680 else "max-width: var(--text-width) found"
    else:
        detail = "No max-width: 680px or max-width: var(--text-width) found in CSS"
    return {"pass": passed, "detail": detail}


def check_image_accessibility(parser: StoryHTMLParser) -> dict:
    """All <img> tags must have a non-empty alt attribute."""
    if not parser.images:
        return {"pass": True, "detail": "No images found (pass)"}
    violations = [
        i + 1
        for i, img in enumerate(parser.images)
        if img["alt"] is None or img["alt"].strip() == ""
    ]
    passed = len(violations) == 0
    if passed:
        return {
            "pass": True,
            "detail": f"All {len(parser.images)} image(s) have non-empty alt attributes",
        }
    return {
        "pass": False,
        "detail": f"{len(violations)} image(s) missing non-empty alt attribute (positions: {violations})",
    }


def check_image_lazy_loading(parser: StoryHTMLParser) -> dict:
    """All <img> tags must have loading='lazy' (pass if no images)."""
    if not parser.images:
        return {"pass": True, "detail": "No images found (pass)"}
    violations = [
        i + 1
        for i, img in enumerate(parser.images)
        if img["loading"] != "lazy"
    ]
    passed = len(violations) == 0
    if passed:
        return {
            "pass": True,
            "detail": f"All {len(parser.images)} image(s) have loading='lazy'",
        }
    return {
        "pass": False,
        "detail": f"{len(violations)} image(s) missing loading='lazy' (positions: {violations})",
    }


def check_file_size(file_path: str) -> dict:
    """HTML file must be < 500,000 bytes."""
    size = os.path.getsize(file_path)
    limit = 500_000
    passed = size < limit
    return {
        "pass": passed,
        "detail": (
            f"File size: {size:,} bytes ({size / 1024:.1f} KB)"
            + ("" if passed else f" — exceeds {limit:,} byte limit")
        ),
        "bytes": size,
    }


def check_beat_count(parser: StoryHTMLParser) -> dict:
    """At least 5 <section> elements with 'beat-' in class."""
    count = parser.beat_sections
    passed = count >= 5
    return {
        "pass": passed,
        "detail": (
            f"{count} beat section(s) found (need \u22655)"
            if not passed
            else f"{count} beat section(s) found"
        ),
        "count": count,
    }


def check_og_tags(parser: StoryHTMLParser) -> dict:
    """Both og:title and og:description meta tags must be present."""
    if parser.has_og_title and parser.has_og_description:
        return {"pass": True, "detail": "og:title and og:description both present"}
    missing = []
    if not parser.has_og_title:
        missing.append("og:title")
    if not parser.has_og_description:
        missing.append("og:description")
    return {
        "pass": False,
        "detail": f"Missing OG tag(s): {', '.join(missing)}",
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_checks(file_path: str) -> dict:
    """Parse the HTML file and run all 8 checks. Return structured result."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        html_content = f.read()

    parser = StoryHTMLParser()
    parser.feed(html_content)

    checks = {
        "viewport_meta": check_viewport_meta(parser),
        "font_hierarchy": check_font_hierarchy(parser),
        "text_column_width": check_text_column_width(parser),
        "image_accessibility": check_image_accessibility(parser),
        "image_lazy_loading": check_image_lazy_loading(parser),
        "file_size": check_file_size(file_path),
        "beat_count": check_beat_count(parser),
        "og_tags": check_og_tags(parser),
    }

    total = len(checks)
    passed = sum(1 for c in checks.values() if c["pass"])
    all_pass = passed == total

    return {
        "file": file_path,
        "score": f"{passed}/{total}",
        "passed": passed,
        "total": total,
        "all_pass": all_pass,
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------


def write_markdown_report(result: dict, report_path: str) -> None:
    """Write a human-readable markdown QA report."""
    status = "PASS" if result["all_pass"] else "ISSUES FOUND"
    lines = [
        "# QA Report — Visual Story Engine",
        "",
        f"**File:** `{result['file']}`",
        f"**Score:** {result['score']}",
        f"**Status:** {status}",
        "",
        "## Check Results",
        "",
        "| Check | Status | Detail |",
        "|-------|--------|--------|",
    ]
    for name, data in result["checks"].items():
        icon = "PASS" if data["pass"] else "FAIL"
        detail = data.get("detail", "")
        lines.append(f"| `{name}` | {icon} | {detail} |")

    lines.append("")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def print_human_readable(result: dict) -> None:
    """Print a human-readable summary to stdout."""
    status = "PASS" if result["all_pass"] else "ISSUES FOUND"
    print(f"\nQA Check: {result['file']}")
    print(f"Score:     {result['score']}  [{status}]")
    print("-" * 60)
    for name, data in result["checks"].items():
        icon = "[PASS]" if data["pass"] else "[FAIL]"
        print(f"  {icon}  {name:<25}  {data.get('detail', '')}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate story.html against Quality Rubric criteria."
    )
    parser.add_argument("html_file", help="Path to the story.html file to check")
    parser.add_argument(
        "--json", action="store_true", help="Output results as JSON (no report written)"
    )
    args = parser.parse_args()

    if not os.path.isfile(args.html_file):
        msg = f"Error: File not found: {args.html_file}"
        if args.json:
            print(json.dumps({"error": msg}))
        else:
            print(msg, file=sys.stderr)
        return 1

    result = run_checks(args.html_file)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human_readable(result)
        # Determine report path relative to this script's project root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        report_path = os.path.join(project_root, "output", "qa", "qa_report.md")
        write_markdown_report(result, report_path)
        print(f"Report written to: {report_path}")

    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
