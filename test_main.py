from collections import Counter
from datetime import date
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest

from main import AUTH_ADMIN, AUTH_ADMIN_KEEP, build_rules_file, create_rules_file, get_matching_sections


class PkActionRulesTest(unittest.TestCase):
    def test_get_matching_sections_ignores_spaces_and_counts_each_value(self):
        text = """org.example.admin:
  implicit active:   auth_admin
  annotation:        org.freedesktop.policykit.exec.path -> /usr/bin/admin

org.example.keep:
  implicit active:auth_admin_keep

org.example.no:
  implicit active:   yes
"""

        sections, counts = get_matching_sections(text)

        self.assertEqual([section[0] for section in sections], ["org.example.admin:", "org.example.keep:"])
        self.assertEqual(counts, Counter({AUTH_ADMIN: 1, AUTH_ADMIN_KEEP: 1}))


    def test_build_rules_file_uses_sample_format(self):
        text = """org.example.admin:
  implicit active:   auth_admin
  annotation:        org.freedesktop.policykit.exec.path -> /usr/bin/admin
  annotation:        org.freedesktop.policykit.exec.allow_gui -> true

org.example.keep:
  implicit active:   auth_admin_keep
"""

        sections, _ = get_matching_sections(text)
        rules = build_rules_file(sections)

        self.assertIn('//action.id == "org.example.admin" ||', rules)
        self.assertIn("//implicit active:   auth_admin", rules)
        self.assertIn("//annotation:        org.freedesktop.policykit.exec.path -> /usr/bin/admin", rules)
        self.assertIn('//action.id == "org.example.keep"', rules)
        self.assertNotIn('//action.id == "org.example.keep" ||', rules)
        self.assertIn("//implicit active:   auth_admin_keep", rules)
        self.assertIn('subject.isInGroup("superuser")', rules)


    def test_create_rules_file_writes_dated_file_and_returns_counts(self):
        with TemporaryDirectory() as directory:
            test_dir = Path(directory)
            (test_dir / "pkaction.txt").write_text(
                """org.example.admin:
  implicit active:   auth_admin

org.example.keep:
  implicit    active:   auth_admin_keep
""",
                encoding="utf-8",
            )

            output_path, counts = create_rules_file(test_dir, date(2026, 7, 5))

            self.assertEqual(output_path, test_dir / "pkaction.2026-07-05.rules")
            self.assertTrue(output_path.exists())
            self.assertEqual(counts, Counter({AUTH_ADMIN: 1, AUTH_ADMIN_KEEP: 1}))


if __name__ == "__main__":
    unittest.main()