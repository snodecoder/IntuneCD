# -*- coding: utf-8 -*-
import unittest
import base64
from pathlib import Path

from testfixtures import TempDirectory

from src.IntuneCD.intunecdlib.documentation_functions import (
    detect_script_language,
    wrap_script_in_code_block,
    document_configs,
    md_file,
)


class TestScriptContentMarkdown(unittest.TestCase):
    """Test class for script content markdown handling."""

    def setUp(self):
        self.directory = TempDirectory()
        self.directory.create()
        self.directory.makedir("config")

    def tearDown(self):
        self.directory.cleanup()

    def test_detect_powershell_language(self):
        """PowerShell script should be detected correctly."""
        powershell_script = """param(
    [string]$Name
)
Write-Host "Hello $Name"
Get-Process"""

        self.assertEqual(detect_script_language(powershell_script), "powershell")

    def test_detect_bash_language_with_shebang(self):
        """Bash script with shebang should be detected correctly."""
        bash_script = """#!/bin/bash
echo "Hello World"
if [ -f /etc/passwd ]; then
    echo "File exists"
fi"""

        self.assertEqual(detect_script_language(bash_script), "bash")

    def test_detect_bash_language_without_shebang(self):
        """Bash script without shebang should be detected correctly."""
        bash_script = """function hello() {
    echo "Hello World"
}
if [ $# -gt 0 ]; then
    hello
fi"""

        self.assertEqual(detect_script_language(bash_script), "bash")

    def test_detect_python_language(self):
        """Python script should be detected correctly."""
        python_script = """#!/usr/bin/env python3
import sys
print("Hello World")"""

        self.assertEqual(detect_script_language(python_script), "python")

    def test_detect_unknown_language(self):
        """Unknown script should return empty string."""
        unknown_script = """This is just plain text
with no recognizable script patterns"""

        self.assertEqual(detect_script_language(unknown_script), "")

    def test_wrap_script_in_code_block_powershell(self):
        """PowerShell script should be wrapped in code block with powershell syntax."""
        powershell_script = "Write-Host 'Hello World'"
        result = wrap_script_in_code_block(powershell_script)

        self.assertIn("<details>", result)
        self.assertIn("<summary>Click to expand script content</summary>", result)
        self.assertIn("```powershell", result)
        self.assertIn("Write-Host 'Hello World'", result)
        self.assertIn("```", result)
        self.assertIn("</details>", result)

    def test_wrap_script_in_code_block_bash(self):
        """Bash script should be wrapped in code block with bash syntax."""
        bash_script = "#!/bin/bash\necho 'Hello World'"
        result = wrap_script_in_code_block(bash_script)

        self.assertIn("```bash", result)
        self.assertIn("echo 'Hello World'", result)

    def test_document_configs_with_script_content_decode_enabled(self):
        """Script content should be decoded and wrapped when decode is True."""
        # Create a test PowerShell script
        powershell_script = "Write-Host 'Test Script'\nGet-Process"
        encoded_script = base64.b64encode(powershell_script.encode("utf-8")).decode("utf-8")

        # Create a test config with script content
        config_data = {
            "@odata.type": "test",
            "displayName": "Test PowerShell Script",
            "description": "Test description",
            "scriptContent": encoded_script,
            "fileName": "test.ps1"
        }

        import json
        self.directory.write(
            "config/test_script.json",
            json.dumps(config_data),
            encoding="utf-8",
        )

        # Document the configs with decode enabled
        document_configs(
            f"{self.directory.path}/config",
            f"{self.directory.path}/test.md",
            "test",
            max_length=None,
            split=False,
            cleanup=False,
            decode=True,
        )

        # Read the generated markdown
        with open(f"{self.directory.path}/test.md", "r", encoding="utf-8") as f:
            content = f.read()

        # Verify script content is properly wrapped
        self.assertIn("<details>", content)
        self.assertIn("<summary>Click to expand script content</summary>", content)
        self.assertIn("```powershell", content)
        self.assertIn("Write-Host 'Test Script'", content)
        self.assertIn("Get-Process", content)
        self.assertIn("</details>", content)

    def test_document_configs_with_script_content_decode_disabled(self):
        """Script content should remain base64 encoded when decode is False."""
        # Create a test PowerShell script
        powershell_script = "Write-Host 'Test Script'"
        encoded_script = base64.b64encode(powershell_script.encode("utf-8")).decode("utf-8")

        # Create a test config with script content
        config_data = {
            "@odata.type": "test",
            "displayName": "Test PowerShell Script",
            "description": "Test description",
            "scriptContent": encoded_script,
            "fileName": "test.ps1"
        }

        import json
        self.directory.write(
            "config/test_script.json",
            json.dumps(config_data),
            encoding="utf-8",
        )

        # Document the configs with decode disabled
        document_configs(
            f"{self.directory.path}/config",
            f"{self.directory.path}/test.md",
            "test",
            max_length=None,
            split=False,
            cleanup=False,
            decode=False,
        )

        # Read the generated markdown
        with open(f"{self.directory.path}/test.md", "r", encoding="utf-8") as f:
            content = f.read()

        # Verify script content is still base64 encoded
        self.assertIn(encoded_script, content)
        self.assertNotIn("Write-Host 'Test Script'", content)
        self.assertNotIn("```powershell", content)

    def test_document_configs_with_remediation_script_content(self):
        """Remediation script content fields should be decoded and wrapped."""
        # Create test detection and remediation scripts
        detection_script = "if (Get-Process -Name 'badprocess' -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }"
        remediation_script = "Stop-Process -Name 'badprocess' -Force"

        encoded_detection = base64.b64encode(detection_script.encode("utf-8")).decode("utf-8")
        encoded_remediation = base64.b64encode(remediation_script.encode("utf-8")).decode("utf-8")

        # Create a test config with remediation scripts
        config_data = {
            "@odata.type": "test",
            "displayName": "Test Remediation Script",
            "description": "Test description",
            "detectionScriptContent": encoded_detection,
            "remediationScriptContent": encoded_remediation
        }

        import json
        self.directory.write(
            "config/test_remediation.json",
            json.dumps(config_data),
            encoding="utf-8",
        )

        # Document the configs with decode enabled
        document_configs(
            f"{self.directory.path}/config",
            f"{self.directory.path}/test.md",
            "test",
            max_length=None,
            split=False,
            cleanup=False,
            decode=True,
        )

        # Read the generated markdown
        with open(f"{self.directory.path}/test.md", "r", encoding="utf-8") as f:
            content = f.read()

        # Verify both scripts are properly wrapped
        self.assertIn("Get-Process -Name 'badprocess'", content)
        self.assertIn("Stop-Process -Name 'badprocess'", content)
        self.assertEqual(content.count("```powershell"), 2)  # Should have 2 PowerShell code blocks

    def test_markdown_special_characters_in_script(self):
        """Scripts with markdown special characters should not break markdown syntax."""
        # Create a script with markdown special characters
        script_with_special_chars = """# This is a comment
$variable = "test_with_underscores"
# Another comment with *asterisks*
Write-Host "Value: $variable"
if ($condition) {
    # [Brackets] and {braces}
    Write-Host "Success!"
}"""

        encoded_script = base64.b64encode(script_with_special_chars.encode("utf-8")).decode("utf-8")

        config_data = {
            "@odata.type": "test",
            "displayName": "Test Script with Special Chars",
            "description": "Test description",
            "scriptContent": encoded_script
        }

        import json
        self.directory.write(
            "config/test_special.json",
            json.dumps(config_data),
            encoding="utf-8",
        )

        # Document the configs with decode enabled
        document_configs(
            f"{self.directory.path}/config",
            f"{self.directory.path}/test.md",
            "test",
            max_length=None,
            split=False,
            cleanup=False,
            decode=True,
        )

        # Read the generated markdown
        with open(f"{self.directory.path}/test.md", "r", encoding="utf-8") as f:
            content = f.read()

        # Verify all special characters are present in the script content
        self.assertIn("test_with_underscores", content)
        self.assertIn("[Brackets] and {braces}", content)
        self.assertIn("*asterisks*", content)

        # Verify the script is wrapped in code block which protects special chars
        self.assertIn("```powershell", content)

    def test_shell_script_detection(self):
        """Shell script should be detected correctly."""
        shell_script = """#!/bin/sh
if [ -d /tmp ]; then
    echo "Directory exists"
fi"""

        result = detect_script_language(shell_script)
        self.assertEqual(result, "bash")


if __name__ == "__main__":
    unittest.main()
