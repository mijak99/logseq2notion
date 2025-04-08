import unittest
from logseq_to_obsidian import from_logseq_line

class TestFromLogseqLine(unittest.TestCase):
    def test_remove_leading_bullets(self):
        self.assertEqual(from_logseq_line("- This is a test"), "This is a test")
        self.assertEqual(from_logseq_line("  - Indented bullet"), "  - Indented bullet")
        self.assertEqual(from_logseq_line("No bullet here"), "No bullet here")

    def test_replace_todo_items(self):
        self.assertEqual(from_logseq_line("- TODO Task 1"), "- [ ] Task 1")
        self.assertEqual(from_logseq_line("- DOING Task 2"), "- [/] Task 2")
        self.assertEqual(from_logseq_line("- DONE Task 3"), "- [x] Task 3")
        self.assertEqual(from_logseq_line("- WAITING Task 4"), "- [ ] Task 4")
        self.assertEqual(from_logseq_line("- NOW Task 5"), "- [ ] Task 5")
        self.assertEqual(from_logseq_line("- LATER Task 6"), "- [ ] Task 6")

    def test_combined_processing(self):
        self.assertEqual(from_logseq_line("- TODO - This is a test"), "- [ ] This is a test")
        self.assertEqual(from_logseq_line("   - TODO Indented"), "   - [ ] Indented")
        self.assertEqual(from_logseq_line("    	- TODO prep an agenda"), "    	- [ ] prep an agenda")
        self.assertEqual(from_logseq_line("		- TODO indented."), "		- [ ] indented.")
        self.assertEqual(from_logseq_line("- DONE - Another test"), "- [x] Another test")
        self.assertEqual(from_logseq_line("  - WAITING Indented task"), "  - [ ] Indented task")

    def test_no_processing_needed(self):
        self.assertEqual(from_logseq_line("This is a normal line"), "This is a normal line")
        self.assertEqual(from_logseq_line("  Indented line"), "  Indented line")

if __name__ == "__main__":
    unittest.main()



