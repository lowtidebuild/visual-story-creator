"""
Tests for qa-check.py
Run with: python3 scripts/test_qa_check.py
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "qa-check.py")
PYTHON = sys.executable


def run_qa(html_content: str, extra_args: list[str] | None = None) -> tuple[int, dict]:
    """Write html_content to a temp file, run qa-check.py --json, return (exit_code, result_dict)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        f.write(html_content)
        tmp_path = f.name

    try:
        cmd = [PYTHON, SCRIPT_PATH, tmp_path, "--json"]
        if extra_args:
            cmd.extend(extra_args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            data = {}
        return result.returncode, data
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Minimal HTML helpers
# ---------------------------------------------------------------------------

VIEWPORT_TAG = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
OG_TAGS = (
    '<meta property="og:title" content="Test Story">\n'
    '<meta property="og:description" content="Test description">'
)
FONT_HIERARCHY = """
<style>
  h1 { font-size: 2.5rem; }
  h2 { font-size: 1.5rem; }
  p  { font-size: 1rem; }
</style>
"""
TEXT_WIDTH = "<style>article { max-width: 680px; margin: 0 auto; }</style>"
BEAT_SECTIONS = "\n".join(
    f'<section class="beat-{i} narrative">Section {i}</section>'
    for i in range(1, 6)
)


def make_html(
    viewport: bool = True,
    og: bool = True,
    fonts: str = FONT_HIERARCHY,
    text_width: bool = True,
    images: str = "",
    beats: str = BEAT_SECTIONS,
    extra_head: str = "",
    extra_body: str = "",
) -> str:
    vp = VIEWPORT_TAG if viewport else ""
    og_block = OG_TAGS if og else ""
    tw = TEXT_WIDTH if text_width else ""
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  {vp}
  {og_block}
  {fonts}
  {tw}
  {extra_head}
</head>
<body>
  {beats}
  {images}
  {extra_body}
</body>
</html>"""


def fully_passing_html() -> str:
    """A minimal complete HTML that should pass all 8 checks."""
    images = (
        '<img src="hero.jpg" alt="Hero image" loading="lazy">\n'
        '<img src="inline.jpg" alt="Inline photo" loading="lazy">'
    )
    return make_html(images=images)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestViewportMeta(unittest.TestCase):

    def test_detects_missing_viewport(self):
        """HTML without viewport meta → viewport_meta check fails."""
        html = make_html(viewport=False)
        code, data = run_qa(html)
        self.assertFalse(data["checks"]["viewport_meta"]["pass"])
        self.assertEqual(code, 1)

    def test_detects_valid_viewport(self):
        """HTML with proper viewport meta → viewport_meta check passes."""
        html = fully_passing_html()
        _, data = run_qa(html)
        self.assertTrue(data["checks"]["viewport_meta"]["pass"])


class TestFontHierarchy(unittest.TestCase):

    def test_detects_missing_font_hierarchy(self):
        """HTML with only 1 font-size value → font_hierarchy check fails."""
        bad_fonts = "<style>* { font-size: 1rem; }</style>"
        html = make_html(fonts=bad_fonts)
        code, data = run_qa(html)
        self.assertFalse(data["checks"]["font_hierarchy"]["pass"])
        self.assertEqual(code, 1)

    def test_detects_valid_font_hierarchy(self):
        """HTML with 3 distinct font-size values → font_hierarchy check passes."""
        html = fully_passing_html()
        _, data = run_qa(html)
        self.assertTrue(data["checks"]["font_hierarchy"]["pass"])


class TestTextColumnWidth(unittest.TestCase):

    def test_detects_missing_text_column_width(self):
        """HTML without max-width 680px or var(--text-width) → check fails."""
        html = make_html(text_width=False)
        code, data = run_qa(html)
        self.assertFalse(data["checks"]["text_column_width"]["pass"])
        self.assertEqual(code, 1)

    def test_detects_css_variable_text_width(self):
        """HTML with var(--text-width) in max-width → check passes."""
        extra = "<style>.article { max-width: var(--text-width); }</style>"
        html = make_html(text_width=False, extra_head=extra)
        _, data = run_qa(html)
        self.assertTrue(data["checks"]["text_column_width"]["pass"])


class TestImageAccessibility(unittest.TestCase):

    def test_detects_missing_alt(self):
        """img tag without alt attribute → image_accessibility fails."""
        images = '<img src="photo.jpg" loading="lazy">'
        html = make_html(images=images)
        code, data = run_qa(html)
        self.assertFalse(data["checks"]["image_accessibility"]["pass"])
        self.assertEqual(code, 1)

    def test_detects_empty_alt(self):
        """img tag with empty alt attribute → image_accessibility fails."""
        images = '<img src="photo.jpg" alt="" loading="lazy">'
        html = make_html(images=images)
        code, data = run_qa(html)
        self.assertFalse(data["checks"]["image_accessibility"]["pass"])

    def test_detects_valid_alt(self):
        """All img tags have non-empty alt → image_accessibility passes."""
        images = '<img src="photo.jpg" alt="A photo" loading="lazy">'
        html = make_html(images=images)
        _, data = run_qa(html)
        self.assertTrue(data["checks"]["image_accessibility"]["pass"])

    def test_no_images_passes(self):
        """No img tags at all → both image checks pass."""
        html = make_html(images="")
        _, data = run_qa(html)
        self.assertTrue(data["checks"]["image_accessibility"]["pass"])


class TestImageLazyLoading(unittest.TestCase):

    def test_detects_missing_lazy(self):
        """img without loading=lazy → image_lazy_loading fails."""
        images = '<img src="photo.jpg" alt="Photo">'
        html = make_html(images=images)
        code, data = run_qa(html)
        self.assertFalse(data["checks"]["image_lazy_loading"]["pass"])
        self.assertEqual(code, 1)

    def test_detects_valid_lazy(self):
        """All img tags have loading=lazy → image_lazy_loading passes."""
        images = '<img src="photo.jpg" alt="Photo" loading="lazy">'
        html = make_html(images=images)
        _, data = run_qa(html)
        self.assertTrue(data["checks"]["image_lazy_loading"]["pass"])

    def test_no_images_passes(self):
        """No img tags → lazy loading check passes."""
        html = make_html(images="")
        _, data = run_qa(html)
        self.assertTrue(data["checks"]["image_lazy_loading"]["pass"])


class TestFileSize(unittest.TestCase):

    def test_detects_file_size_over_limit(self):
        """HTML > 500KB → file_size check fails."""
        # 501 KB of filler
        filler = "<!-- " + ("x" * 1020) + " -->\n"
        big_extra = filler * 500  # ~500KB of comments
        html = make_html(extra_body=big_extra)
        code, data = run_qa(html)
        self.assertFalse(data["checks"]["file_size"]["pass"])
        self.assertEqual(code, 1)

    def test_normal_file_passes(self):
        """Normal-sized HTML → file_size passes."""
        html = fully_passing_html()
        _, data = run_qa(html)
        self.assertTrue(data["checks"]["file_size"]["pass"])


class TestBeatCount(unittest.TestCase):

    def test_detects_beats(self):
        """HTML with 5 beat sections → beat_count passes."""
        html = fully_passing_html()
        _, data = run_qa(html)
        self.assertTrue(data["checks"]["beat_count"]["pass"])

    def test_detects_too_few_beats(self):
        """HTML with only 2 beat sections → beat_count fails."""
        two_beats = (
            '<section class="beat-1">Beat 1</section>\n'
            '<section class="beat-2">Beat 2</section>'
        )
        html = make_html(beats=two_beats)
        code, data = run_qa(html)
        self.assertFalse(data["checks"]["beat_count"]["pass"])
        self.assertEqual(code, 1)

    def test_non_beat_sections_not_counted(self):
        """Sections without beat- in class are not counted."""
        sections = (
            '<section class="intro">Intro</section>\n'
            '<section class="outro">Outro</section>'
        )
        html = make_html(beats=sections)
        code, data = run_qa(html)
        self.assertFalse(data["checks"]["beat_count"]["pass"])
        self.assertEqual(code, 1)


class TestOgTags(unittest.TestCase):

    def test_detects_missing_og_tags(self):
        """HTML without OG meta tags → og_tags check fails."""
        html = make_html(og=False)
        code, data = run_qa(html)
        self.assertFalse(data["checks"]["og_tags"]["pass"])
        self.assertEqual(code, 1)

    def test_detects_valid_og_tags(self):
        """HTML with og:title and og:description → og_tags passes."""
        html = fully_passing_html()
        _, data = run_qa(html)
        self.assertTrue(data["checks"]["og_tags"]["pass"])

    def test_detects_partial_og_tags(self):
        """HTML with only og:title (no og:description) → og_tags fails."""
        extra = '<meta property="og:title" content="Test">'
        html = make_html(og=False, extra_head=extra)
        code, data = run_qa(html)
        self.assertFalse(data["checks"]["og_tags"]["pass"])
        self.assertEqual(code, 1)


class TestFullPassingHtml(unittest.TestCase):

    def test_full_passing_html(self):
        """A minimal but complete HTML that passes all 8 checks."""
        html = fully_passing_html()
        code, data = run_qa(html)
        self.assertEqual(data["passed"], 8)
        self.assertEqual(data["total"], 8)
        self.assertTrue(data["all_pass"])
        self.assertEqual(code, 0)
        # Verify all individual checks pass
        for check_name, result in data["checks"].items():
            self.assertTrue(result["pass"], f"Check '{check_name}' failed: {result.get('detail')}")


class TestJsonOutput(unittest.TestCase):

    def test_json_output_structure(self):
        """--json flag produces correct JSON structure."""
        html = fully_passing_html()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html)
            tmp_path = f.name
        try:
            result = subprocess.run(
                [PYTHON, SCRIPT_PATH, tmp_path, "--json"],
                capture_output=True, text=True
            )
            data = json.loads(result.stdout)
            self.assertIn("file", data)
            self.assertIn("score", data)
            self.assertIn("passed", data)
            self.assertIn("total", data)
            self.assertIn("all_pass", data)
            self.assertIn("checks", data)
            # score format "X/8"
            self.assertRegex(data["score"], r"^\d+/8$")
        finally:
            os.unlink(tmp_path)

    def test_human_readable_output_writes_report(self):
        """Without --json flag, writes output/qa/qa_report.md."""
        html = fully_passing_html()
        project_root = os.path.dirname(os.path.dirname(SCRIPT_PATH))
        report_path = os.path.join(project_root, "output", "qa", "qa_report.md")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html)
            tmp_path = f.name
        try:
            subprocess.run(
                [PYTHON, SCRIPT_PATH, tmp_path],
                capture_output=True, text=True
            )
            self.assertTrue(
                os.path.exists(report_path),
                f"Report not found at {report_path}"
            )
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
