from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/query-tvcmall-customer-data"
ENDPOINT = "https://mcpserver.tvc-mall.com"


class SkillContractTests(unittest.TestCase):
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

    def test_no_old_endpoint_or_plausible_real_pat(self) -> None:
        deliverables = [ROOT / "README.md", ROOT / "AGENTS.md", *SKILL.rglob("*")]
        repository_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in deliverables
            if path.is_file() and "__pycache__" not in path.parts
        )
        forbidden_host = ".".join(("115", "175", "225", "101"))
        self.assertNotIn(forbidden_host, repository_text)
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
            "商品",
            "订单",
            "物流",
            "积分",
            "余额",
            "安全",
            "验证",
            "贡献",
        )
        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)
        forbidden_host = ".".join(("115", "175", "225", "101"))
        self.assertNotIn(forbidden_host, text)
