"""The locked table shows a word card's resolved definition.

Run: python3 -m unittest discover -s tests -v
"""
import importlib.util
from pathlib import Path
import unittest

SK = Path(__file__).resolve().parent.parent / "skills" / "grill-me-page"
spec = importlib.util.spec_from_file_location("grill_build", SK / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class LockedTable(unittest.TestCase):
    def test_shows_resolved_words(self):
        table = build.locked_table(build.load_record(str(SK / "example" / "answers-v1.json")), {"W1"})
        self.assertIn("<b>Close</b>: The time the board stops taking orders for tomorrow.", table)
        self.assertIn("<b>Cutoff</b>: The café&#x27;s own limit for our order, 10:00", table)  # the person's words, not the proposal
        self.assertEqual(table.count("written to glossary ✓"), 1)
        self.assertIn("Everyone on site", table)  # ordinary rows unchanged


if __name__ == "__main__":
    unittest.main()
