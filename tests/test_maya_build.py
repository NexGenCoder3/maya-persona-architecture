import tempfile
import unittest
from pathlib import Path

import maya_build


class PromptBuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.persona = self.root / "persona"
        self.frameworks = self.root / "frameworks"
        self.persona.mkdir()
        self.frameworks.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_module_order_is_deterministic(self):
        (self.persona / "system_prompt.md").write_text("BASE", encoding="utf-8")
        (self.frameworks / "zeta.md").write_text("Z", encoding="utf-8")
        (self.frameworks / "alpha.md").write_text("A", encoding="utf-8")
        compiled = maya_build.assemble_prompt(self.frameworks, self.persona)
        self.assertLess(compiled.index("MODULE: ALPHA.MD"), compiled.index("MODULE: ZETA.MD"))

    def test_trailing_whitespace_is_removed_from_compiled_markdown(self):
        (self.persona / "system_prompt.md").write_text("BASE  \n", encoding="utf-8")
        (self.frameworks / "module.md").write_text("MODULE TEXT  \n", encoding="utf-8")
        compiled = maya_build.assemble_prompt(self.frameworks, self.persona)
        self.assertTrue(all(line == line.rstrip() for line in compiled.splitlines()))

    def test_missing_base_prompt_fails_instead_of_becoming_prompt_text(self):
        with self.assertRaises(FileNotFoundError):
            maya_build.assemble_prompt(self.frameworks, self.persona)

    def test_missing_selected_module_fails(self):
        (self.persona / "system_prompt.md").write_text("BASE", encoding="utf-8")
        with self.assertRaises(FileNotFoundError):
            maya_build.assemble_prompt(self.frameworks, self.persona, ["missing.md"])

    def test_module_path_cannot_escape_framework_directory(self):
        (self.persona / "system_prompt.md").write_text("BASE", encoding="utf-8")
        outside = self.root / "secret.md"
        outside.write_text("secret", encoding="utf-8")
        with self.assertRaises(ValueError):
            maya_build.assemble_prompt(self.frameworks, self.persona, ["../secret.md"])


if __name__ == "__main__":
    unittest.main()
