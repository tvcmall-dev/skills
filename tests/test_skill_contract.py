from __future__ import annotations

from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/query-tvcmall-customer-data"
ENDPOINT = "https://openai.tvc-mall.com/mcp"
OLD_ENDPOINTS = (
    "https://openapi.tvc-mall.com/mcp",
    "https://mcpserver.tvc-mall.com",
)
TOOLS = (
    "tvcmall_auth_status",
    "tvcmall_search_products",
    "tvcmall_get_product_detail",
    "tvcmall_estimate_shipping",
    "tvcmall_list_orders",
    "tvcmall_get_order_detail",
    "tvcmall_get_tracking_info",
    "tvcmall_batch_get_tracking",
    "tvcmall_get_points",
    "tvcmall_list_point_records",
    "tvcmall_get_balance",
    "tvcmall_list_balance_records",
)


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
        self.assertNotIn("\n      headers:", text)
        self.assertIn("$query-tvcmall-customer-data", text)

    def test_skill_links_live_references_and_setup_script(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for relative in (
            "references/mcp-setup.md",
            "references/tool-routing.md",
            "scripts/configure_tvcmall_mcp.py",
        ):
            self.assertIn(relative, text)
            self.assertTrue((SKILL / relative).exists())
        self.assertNotIn("references/tool-reference.md", text)
        self.assertFalse((SKILL / "references/tool-reference.md").exists())

    def test_references_close_key_and_query_routing_gaps(self) -> None:
        setup = (SKILL / "references/mcp-setup.md").read_text(encoding="utf-8")
        routing = (SKILL / "references/tool-routing.md").read_text(encoding="utf-8")
        for value in ("revoke it immediately", "request a new Key", "do not repeat it"):
            with self.subTest(value=value):
                self.assertIn(value, setup)
        self.assertIn("Do not let another process edit", setup)
        for value in (
            "tmcp_catalog.read",
            "catalog.read",
            "Only after a catalog query returns `401`",
        ):
            with self.subTest(value=value):
                self.assertIn(value, setup)
        for value in (
            "current MCP tool schema",
            "without asking the user to apply for a personal Key first",
            "If a product or shipping tool returns `AUTH_REQUIRED`",
            "Account tools require a personal Key",
        ):
            with self.subTest(value=value):
                self.assertIn(value, routing)

    def test_tool_parameters_come_from_current_mcp_schema(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        routing = (SKILL / "references/tool-routing.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for value in (
            "Inspect the current MCP tool schema before every tool call",
            "required inputs, types, allowed values, defaults, and limits",
            "Do not use static documentation as the tool parameter contract",
        ):
            with self.subTest(value=value):
                self.assertIn(value, skill)

        self.assertIn("| Category | Tool | Capability |", readme)
        self.assertNotIn("External Parameters", readme)
        self.assertNotIn("Tool Parameter Reference", readme)
        self.assertNotIn("tool-reference.md", readme)
        for stale_contract in (
            "page=1",
            "page_size=20",
            "page_size=10",
            "no more than 50",
            "V3All",
            "When `direction` is omitted",
        ):
            with self.subTest(stale_contract=stale_contract):
                self.assertNotIn(stale_contract, routing)

    def test_personal_key_configuration_uses_visible_system_terminal(self) -> None:
        setup = (SKILL / "references/mcp-setup.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for value in (
            "visible operating-system terminal",
            "Do not use an Agent client's embedded PTY",
            "Start-Process",
            "-WindowStyle Normal",
            "Do not pass the Key as a command-line argument or environment variable",
            "non-sensitive",
            "open a system terminal manually",
        ):
            with self.subTest(value=value):
                self.assertIn(value, setup)

        self.assertIn("visible operating-system terminal", readme)
        self.assertIn("embedded PTY", readme)

    def test_balance_summary_routes_to_account_stat(self) -> None:
        routing = (SKILL / "references/tool-routing.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "| View the current balance summary | `tvcmall_get_balance` |",
            routing,
        )
        self.assertIn("`GET api/v3/user/points/stat?type=balance`", routing)
        self.assertIn(
            "| View balance records | `tvcmall_list_balance_records` |",
            routing,
        )
        self.assertIn("Do not call the WebApi route directly", routing)
        self.assertIn(
            "| Balance | `tvcmall_get_balance` | Retrieves the available and frozen balance summary; requires a personal Key |",
            readme,
        )

    def test_readme_lists_all_supported_tools(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for tool in TOOLS:
            with self.subTest(tool=tool):
                self.assertIn(f"`{tool}`", text)

    def test_readme_lists_skill_installation_options_for_agent_tools(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        required = (
            "Install This Skill In Agent Tools",
            "git clone https://github.com/tvcmall-dev/skills.git",
            ".agents/skills/query-tvcmall-customer-data",
            "Codex CLI",
            "$HOME/.agents/skills/query-tvcmall-customer-data",
            "$query-tvcmall-customer-data",
            "Claude Code / Claude Code CLI",
            "$HOME/.claude/skills/query-tvcmall-customer-data",
            "/query-tvcmall-customer-data",
            "Gemini CLI",
            "$HOME/.gemini/skills/query-tvcmall-customer-data",
            "gemini skills list",
            "GitHub Copilot CLI",
            "$HOME/.copilot/skills/query-tvcmall-customer-data",
            "/skills reload",
            "Cursor CLI",
            ".cursor/skills/query-tvcmall-customer-data",
            "Qwen Code CLI",
            ".qwen/skills/query-tvcmall-customer-data",
            "https://learn.chatgpt.com/docs/build-skills",
            "https://code.claude.com/docs/en/skills",
            "https://geminicli.com/docs/cli/skills/",
            "https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills",
            "https://cursor.com/docs/skills",
            "https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/",
        )
        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

        forbidden = (
            "Agent Tool Installation",
            "npm install -g @openai/codex",
            "npm install -g @anthropic-ai/claude-code",
            "npm install -g @google/gemini-cli",
            "npm install -g @github/copilot",
            "winget install GitHub.Copilot",
        )
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, text)

    def test_scoped_documentation_is_english_except_agents_md(self) -> None:
        paths = (
            ROOT / "README.md",
            SKILL / "SKILL.md",
            SKILL / "agents/openai.yaml",
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
        delivery_files = [ROOT / "README.md", *SKILL.rglob("*")]
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
        for old_endpoint in OLD_ENDPOINTS:
            self.assertNotIn(old_endpoint, delivery_text)
        self.assertNotIn("http://openai.tvc-mall.com", delivery_text)
        self.assertNotIn(f"{ENDPOINT}/mcp", delivery_text)
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
            "tmcp_catalog.read",
            "catalog.read",
            "401",
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
        for old_endpoint in OLD_ENDPOINTS:
            self.assertNotIn(old_endpoint, text)
