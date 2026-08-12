from __future__ import annotations

from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/query-tvcmall-customer-data"
ENDPOINT = "https://mcpserver.tvc-mall.com"


class SkillContractTests(unittest.TestCase):
    def test_local_project_guidance_is_ignored_and_untracked(self) -> None:
        for relative in (
            "AGENTS.md",
            "docs/superpowers/specs/2026-08-12-tvcmall-customer-skill-design.md",
        ):
            with self.subTest(relative=relative):
                ignored = subprocess.run(
                    ["git", "check-ignore", "-q", relative],
                    cwd=ROOT,
                    check=False,
                )
                tracked = subprocess.run(
                    ["git", "ls-files", "--error-unmatch", relative],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                )
                self.assertEqual(ignored.returncode, 0)
                self.assertNotEqual(tracked.returncode, 0)

    def test_frontmatter_contains_only_name_and_description(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        keys = re.findall(r"^([a-z_]+):", frontmatter, re.MULTILINE)
        self.assertEqual(keys, ["name", "description"])
        self.assertIn("configure TVCMALL_API_KEY", frontmatter)

    def test_openai_yaml_declares_exact_tvcmall_dependency(self) -> None:
        text = (SKILL / "agents/openai.yaml").read_text(encoding="utf-8")
        self.assertIn('value: "tvcmall"', text)
        self.assertIn('transport: "streamable_http"', text)
        self.assertIn(f'url: "{ENDPOINT}"', text)
        self.assertIn("$query-tvcmall-customer-data", text)

    def test_skill_links_both_references_and_setup_script(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for relative in (
            "references/mcp-setup.md",
            "references/tool-routing.md",
            "scripts/configure_tvcmall_mcp.py",
        ):
            self.assertIn(relative, text)
            self.assertTrue((SKILL / relative).exists())

    def test_references_close_key_and_query_routing_gaps(self) -> None:
        setup = (SKILL / "references/mcp-setup.md").read_text(encoding="utf-8")
        routing = (SKILL / "references/tool-routing.md").read_text(encoding="utf-8")
        for value in ("revoke it immediately", "request a new Key", "do not repeat it"):
            with self.subTest(value=value):
                self.assertIn(value, setup)
        self.assertIn("Do not let another process edit", setup)
        for value in (
            "page=1",
            "page_size=20",
            "page_size=10",
            "do not claim that results are strictly sorted by time",
            "If `order_id` is missing",
            "When `direction` is omitted, use `all`",
        ):
            with self.subTest(value=value):
                self.assertIn(value, routing)

    def test_scoped_documentation_is_english(self) -> None:
        paths = (
            ROOT / "README.md",
            SKILL / "SKILL.md",
            SKILL / "references/mcp-setup.md",
            SKILL / "references/tool-routing.md",
        )
        for path in paths:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIsNone(re.search(r"[\u3400-\u9fff]", text))

    def test_no_old_endpoint_or_plausible_real_pat(self) -> None:
        tracked = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout.decode("utf-8").split("\0")
        deliverables = [ROOT / relative for relative in tracked if relative]
        delivery_files = [ROOT / "README.md", ROOT / "AGENTS.md", *SKILL.rglob("*")]
        repository_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in deliverables
            if path.is_file() and "__pycache__" not in path.parts
        )
        delivery_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in delivery_files
            if path.is_file() and "__pycache__" not in path.parts
        )
        forbidden_host = ".".join(("115", "175", "225", "101"))
        self.assertNotIn(forbidden_host, delivery_text)
        leaked = re.findall(
            r"tmcp_v1_(?!demo|fake|example)[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
            repository_text,
        )
        self.assertEqual(leaked, [])

    def test_readme_covers_setup_usage_security_and_contributing(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        required = (
            "query-tvcmall-customer-data",
            ENDPOINT,
            "https://www.tvcmall.com/user/agentkeys",
            "TVCMALL_API_KEY",
            "Products",
            "Orders",
            "Tracking",
            "Points",
            "Balance",
            "Security",
            "Validation",
            "Contributing",
        )
        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)
        forbidden_host = ".".join(("115", "175", "225", "101"))
        self.assertNotIn(forbidden_host, text)
