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
        self.assertIn("$query-tvcmall-customer-data", text)

    def test_skill_links_both_references_and_setup_script(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for relative in (
            "references/mcp-setup.md",
            "references/tool-routing.md",
            "references/tool-reference.md",
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

    def test_tool_reference_covers_every_tool_and_webapi_mapping(self) -> None:
        text = (SKILL / "references/tool-reference.md").read_text(encoding="utf-8")
        for tool in TOOLS:
            with self.subTest(tool=tool):
                self.assertIn(f"`{tool}`", text)

        for route in (
            "/v3/product/list/search/mapping",
            "/v3/productdetail/detail",
            "/v3/productdetail/shipping/compute",
            "/v3/user/getorders",
            "/v3/order/detail",
            "/order/getlogisticstracking",
            "/v3/user/points/stat",
            "/v3/user/points/list",
            "/v3/user/balance/list",
        ):
            with self.subTest(route=route):
                self.assertIn(f"`{route}`", text)

        for parameter in (
            "`query`",
            "`product_id`",
            "`sku`",
            "`quantity`",
            "`countrycode`",
            "`status`",
            "`order_id`",
            "`order_ids`",
            "`direction`",
            "`page`",
            "`page_size`",
        ):
            with self.subTest(parameter=parameter):
                self.assertIn(parameter, text)

        self.assertIn("`start_date`", text)
        self.assertIn("`end_date`", text)
        self.assertIn("`BeginDate`", text)
        self.assertIn("`EndDate`", text)
        removed_implementation_note = "\u5f53\u524d MCP Server \u672a\u8f6c\u53d1"
        self.assertNotIn(removed_implementation_note, text)
        self.assertIn("`pointstype=0`", text)
        self.assertIn("`pointstype=1`", text)
        self.assertIn("`pointstype=2`", text)

    def test_readme_lists_all_supported_tools(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for tool in TOOLS:
            with self.subTest(tool=tool):
                self.assertIn(f"`{tool}`", text)

    def test_readme_lists_mainstream_agent_installation_options(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        required = (
            "Agent Tool Installation",
            "Codex CLI",
            "https://learn.chatgpt.com/docs/codex/cli",
            "curl -fsSL https://chatgpt.com/codex/install.sh | sh",
            'powershell -ExecutionPolicy ByPass -c "irm https://chatgpt.com/codex/install.ps1 | iex"',
            "npm install -g @openai/codex",
            "Claude Code / Claude Code CLI",
            "https://code.claude.com/docs/en/setup",
            "curl -fsSL https://claude.ai/install.sh | bash",
            "irm https://claude.ai/install.ps1 | iex",
            "winget install Anthropic.ClaudeCode",
            "npm install -g @anthropic-ai/claude-code",
            "Gemini CLI",
            "https://geminicli.com/docs/get-started/installation/",
            "npm install -g @google/gemini-cli",
            "GitHub Copilot CLI",
            "https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli",
            "npm install -g @github/copilot",
            "winget install GitHub.Copilot",
            "Cursor CLI",
            "https://cursor.com/docs/cli/installation",
            "curl https://cursor.com/install -fsS | bash",
            "irm 'https://cursor.com/install?win32=true' | iex",
            "Qwen Code CLI",
            "https://qwenlm.github.io/qwen-code-docs/en/users/overview/",
            "curl -fsSL https://qwen-code-assets.oss-cn-hangzhou.aliyuncs.com/installation/install-qwen-standalone.sh | bash",
            "irm https://qwen-code-assets.oss-cn-hangzhou.aliyuncs.com/installation/install-qwen-standalone.ps1 | iex",
        )
        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_scoped_documentation_is_english_except_agents_md(self) -> None:
        paths = (
            ROOT / "README.md",
            SKILL / "SKILL.md",
            SKILL / "agents/openai.yaml",
            SKILL / "references/mcp-setup.md",
            SKILL / "references/tool-routing.md",
            SKILL / "references/tool-reference.md",
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
