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
    "tvcmall_get_product_filters",
    "tvcmall_get_product_detail",
    "tvcmall_estimate_shipping",
    "tvcmall_list_orders",
    "tvcmall_get_order_detail",
    "tvcmall_get_tracking_info",
    "tvcmall_batch_get_tracking",
    "tvcmall_get_points",
    "tvcmall_get_balance",
    "tvcmall_list_balance_records",
)
DISABLED_TOOLS = ("tvcmall_list_point_records",)


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

    def test_skill_links_live_references_and_setup_scripts(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for relative in (
            "references/mcp-setup.md",
            "references/tool-routing.md",
            "scripts/configure_tvcmall_mcp_windows.ps1",
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
            "Ask whether the user already has a `TVCMALL_API_KEY`",
            "pause configuration until the user has obtained a Key",
            "complete personal PAT",
        ):
            with self.subTest(value=value):
                self.assertIn(value, setup)
        for value in (
            "current MCP tool schema",
            "Do not call any business tool until",
            "`AUTH_REQUIRED`: guide the user",
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

    def test_relative_image_paths_use_tvcmall_image_origin(self) -> None:
        routing = (SKILL / "references/tool-routing.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        image_origin = "https://img.tvc-mall.com/"
        relative_path = "/uploads/details/6622000996A-5.jpg"
        relative_path_without_leading_slash = "uploads/details/6622000996A-5.jpg"
        display_url = "https://img.tvc-mall.com/uploads/details/6622000996A-5.jpg"
        relative_path_examples = (
            f"Examples: `{relative_path}` and `{relative_path_without_leading_slash}` "
            f"both become `{display_url}`."
        )

        self.assertIn("## MCP Images", routing)
        self.assertIn("any TVCMall MCP tool", routing)
        self.assertIn(image_origin, routing)
        self.assertIn(image_origin, readme)
        self.assertIn(relative_path, routing)
        self.assertIn(display_url, routing)
        self.assertIn(relative_path_examples, routing)
        self.assertIn("exactly one slash", routing)
        self.assertIn("preserve an absolute HTTP or HTTPS URL unchanged", routing)
        self.assertIn(
            "Treat any other non-empty image value as a relative image path",
            routing,
        )
        self.assertIn("Remove its leading slash, if present", routing)
        self.assertIn(
            "Normalize only the displayed URL. Do not modify the raw MCP response "
            "or treat the image origin as part of an MCP tool schema.",
            routing,
        )
        self.assertIn(
            "When any TVCMall MCP tool returns a relative image path",
            readme,
        )
        self.assertIn(
            "Absolute HTTP and HTTPS image URLs remain unchanged.",
            readme,
        )

    def test_personal_key_configuration_uses_native_windows_dialog(self) -> None:
        setup = (SKILL / "references/mcp-setup.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for value in (
            "Windows PowerShell 5.1",
            "Windows Forms",
            "masked by default",
            "does not require or invoke Python",
            "configure_tvcmall_mcp_windows.ps1",
            "Do not use an Agent client's embedded PTY",
            "Start-Process",
            "-WindowStyle Hidden",
            "-NoProfile",
            "-STA",
            "-File",
            "resolved absolute",
            "Do not pass the Key as a command-line argument or environment variable",
            "piped input",
            "Python fallback",
            "visible operating-system terminal",
        ):
            with self.subTest(value=value):
                self.assertIn(value, setup)

        self.assertIn("local masked dialog", readme)
        self.assertIn("Python is not required on Windows", readme)
        self.assertIn("embedded PTY", readme)
        self.assertNotIn(
            "opens a visible operating-system terminal and runs the local configuration script there",
            readme,
        )

    def test_windows_setup_script_has_no_secret_input_channel(self) -> None:
        script_path = SKILL / "scripts/configure_tvcmall_mcp_windows.ps1"
        script = script_path.read_text(encoding="utf-8")

        self.assertIn("System.Windows.Forms", script)
        self.assertIn("UseSystemPasswordChar", script)
        self.assertNotIn("$env:TVCMALL_API_KEY", script)
        self.assertNotIn("Read-Host", script)
        self.assertNotRegex(script, r"(?i)&?\s*(?:pythonw?|py)(?:\.exe)?\b")

    def test_current_balance_routes_to_account_stat(self) -> None:
        routing = (SKILL / "references/tool-routing.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "| View the current balance | `tvcmall_get_balance` |",
            routing,
        )
        self.assertIn("`GET api/v3/user/points/stat?type=balance`", routing)
        self.assertIn(
            "| View balance records | `tvcmall_list_balance_records` |",
            routing,
        )
        self.assertIn("Do not call the WebApi route directly", routing)
        self.assertIn(
            "| Balance | `tvcmall_get_balance` | Retrieves the backend-formatted current balance; requires a personal Key |",
            readme,
        )
        self.assertNotIn("available and frozen balance", readme)

    def test_readme_lists_all_supported_tools(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        routing = (SKILL / "references/tool-routing.md").read_text(encoding="utf-8")
        for tool in TOOLS:
            with self.subTest(tool=tool):
                self.assertIn(f"`{tool}`", readme)
        for tool in DISABLED_TOOLS:
            with self.subTest(disabled_tool=tool):
                self.assertNotIn(tool, readme)
                self.assertNotIn(tool, routing)

    def test_user_visible_capabilities_match_current_mcpserver(self) -> None:
        routing = (SKILL / "references/tool-routing.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for value in (
            "authoritative `total`",
            "`tvcmall_get_product_filters`",
            "Do not guess a filter Code",
            "remaining points",
            "Decimal point values",
            "backend-formatted current balance",
            "do not add currency formatting",
            "`Invalid params`",
            "`SESSION_CAPACITY_REACHED`",
        ):
            with self.subTest(value=value):
                self.assertIn(value, routing)

        for value in (
            "publish-date range",
            "`tvcmall_get_product_filters`",
            "remaining points",
            "backend-formatted current balance",
        ):
            with self.subTest(value=value):
                self.assertIn(value, readme)

    def test_readme_lists_skill_installation_options_for_agent_tools(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        required = (
            "Install This Skill In Agent Tools",
            "git clone https://github.com/tvcmall-dev/skills.git",
            "$REPO_ROOT/.agents/skills/query-tvcmall-customer-data",
            "Codex app / CLI",
            "$CODEX_HOME/skills/query-tvcmall-customer-data",
            "$HOME/.codex/skills/query-tvcmall-customer-data",
            "$HOME/.agents/skills/query-tvcmall-customer-data",
            "$skill-installer",
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
            "Start `codex` from this repository root",
            r"C:\Users\Administrator\.codex\skills",
            "npm install -g @openai/codex",
            "npm install -g @anthropic-ai/claude-code",
            "npm install -g @google/gemini-cli",
            "npm install -g @github/copilot",
            "winget install GitHub.Copilot",
        )
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, text)

    def test_readme_distinguishes_codex_install_locations(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        manual_user_install = (
            "For a manual Codex user-level installation, copy the Skill to "
            "`$HOME/.agents/skills/query-tvcmall-customer-data`."
        )
        installer_managed_install = (
            "The installer places the Skill at "
            "`$CODEX_HOME/skills/query-tvcmall-customer-data`, which defaults to "
            "`$HOME/.codex/skills/query-tvcmall-customer-data` when `CODEX_HOME` "
            "is not set."
        )

        self.assertIn(manual_user_install, text)
        self.assertIn(installer_managed_install, text)

    def test_readme_does_not_require_clone_or_restart_for_codex_installer(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("For manual installation, clone this repository first:", text)
        self.assertIn("The installed Skill is available on the next turn.", text)
        self.assertNotIn("Clone this repository first:", text)
        self.assertNotIn("Start a new Codex session, then invoke", text)

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
        self.assertNotIn("tmcp_catalog.read", delivery_text)
        self.assertNotIn("default `catalog.read`", delivery_text)
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
