from __future__ import annotations

import ast
from pathlib import Path
import unittest


FORBIDDEN_IMPORTS = {
    "imaplib",
    "socket",
    "smtplib",
    "urllib",
    "http.client",
    "requests",
    "httpx",
}


class NoNetworkImplementationTests(unittest.TestCase):
    def test_package_has_no_network_imports(self) -> None:
        source_root = Path(__file__).parents[1] / "src" / "virgilio_connector"
        violations: list[str] = []

        for path in source_root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                else:
                    continue
                for name in names:
                    if any(name == item or name.startswith(f"{item}.") for item in FORBIDDEN_IMPORTS):
                        violations.append(f"{path.name}: {name}")

        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
