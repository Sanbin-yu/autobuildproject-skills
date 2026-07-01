import ast
import os
import stat
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_skill_metadata_exists_and_mentions_diagnosis():
    skill = ROOT / "skills/springboot-project-generator/SKILL.md"

    content = skill.read_text(encoding="utf-8")

    assert "name: springboot-project-generator" in content
    assert "项目问诊" in content
    assert "python3 -m springboot_project_generator generate" in content


def test_repository_readme_documents_cli_and_skill_usage():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "python3 -m springboot_project_generator generate" in readme
    assert "$springboot-project-generator" in readme
    assert "mvn test" in readme
    assert "project.yaml" in readme
    assert "fields:" in readme
    assert "features:" in readme


def test_repository_readme_has_open_source_trust_signals():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

    assert "[![CI]" in readme
    assert "MIT License" in license_text
    assert "## Quick Start" in readme
    assert "pipx run" in readme
    assert "uvx" in readme
    assert "## Supported Scope" in readme
    assert "## Not Supported Yet" in readme
    assert "## Generated Project Shape" in readme
    assert "## Example APIs" in readme
    assert "## Windows / PowerShell" in readme
    assert "Spring Boot 3.x" in readme
    assert "Java 21" in readme
    assert "Maven multi-module" in readme
    assert "当前不是生产级后端生成器" in readme
    assert "默认全功能项目" in readme
    assert "lean 项目" in readme
    assert "examples/club-project.yaml" in readme


def test_python_package_metadata_is_ready_for_v02_installation():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '[build-system]' in pyproject
    assert 'build-backend = "setuptools.build_meta"' in pyproject
    assert 'name = "springboot-project-generator"' in pyproject
    assert 'version = "0.2.0"' in pyproject
    assert 'requires-python = ">=3.11"' in pyproject
    assert (
        'springboot-project-generator = "springboot_project_generator.cli:main"'
        in pyproject
    )


def test_repository_contains_external_templates():
    template_files = [
        ROOT / "templates/maven/root-pom.xml.tpl",
        ROOT / "templates/project/README.md.tpl",
        ROOT / "templates/resources/application.yml.tpl",
    ]

    for template_file in template_files:
        assert template_file.exists(), template_file
        assert "__PROJECT_NAME__" in template_file.read_text(encoding="utf-8")


def test_github_actions_workflow_runs_python_and_generated_project_checks():
    workflow = ROOT / ".github/workflows/ci.yml"

    content = workflow.read_text(encoding="utf-8")

    assert "matrix:" in content
    assert "ubuntu-latest" in content
    assert "windows-latest" in content
    assert "python -m pytest" in content
    assert "PYTHONUTF8" in content
    assert "./scripts/ci-smoke.sh all" in content
    assert "CI_SMOKE_SKIP_MAVEN" not in content


def test_ci_smoke_script_documents_reproducible_generation_checks():
    script = ROOT / "scripts/ci-smoke.sh"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert script.exists()
    assert script.stat().st_mode & stat.S_IXUSR

    content = script.read_text(encoding="utf-8")

    assert "Usage: scripts/ci-smoke.sh [default|lean|all]" in content
    assert "CI_SMOKE_OUTPUT_DIR" in content
    assert "CI_SMOKE_SKIP_MAVEN" in content
    assert "PYTHON_BIN" in content
    assert "command -v python3" in content
    assert "MAVEN_BIN" in content
    assert "command -v mvn" in content
    assert "springboot_project_generator generate" in content
    assert "mvn package" in content
    assert "ci-default" in content
    assert "ci-lean" in content
    assert "HealthController.java" in content
    assert "schema.sql" in content
    assert "scripts/ci-smoke.sh all" in readme


def test_structured_example_config_is_documented():
    example = ROOT / "examples/club-project.yaml"
    examples_readme = (ROOT / "examples/README.md").read_text(encoding="utf-8")
    skill = (ROOT / "skills/springboot-project-generator/SKILL.md").read_text(encoding="utf-8")

    content = example.read_text(encoding="utf-8")

    assert "fields:" in content
    assert "features:" in content
    assert "roles:" in content
    assert "字段级生成" in skill
    assert "技术栈开关" in skill
    assert "python -m springboot_project_generator generate --config examples/club-project.yaml --no-interactive" in examples_readme
    assert "mvn package" in examples_readme
    assert "不会提交完整生成物" in examples_readme


def test_skill_documents_diagnosis_questions_and_yaml_draft_rule():
    skill = (ROOT / "skills/springboot-project-generator/SKILL.md").read_text(encoding="utf-8")

    expected_questions = [
        "项目类型",
        "核心业务对象",
        "对象字段",
        "用户角色",
        "数据持久化",
        "外部服务",
        "安全要求",
    ]

    for question in expected_questions:
        assert question in skill
    assert "先整理 project.yaml 草稿" in skill
    assert "不要直接跳过问诊运行 CLI" in skill


def test_install_skill_script_links_skill_into_codex_home(tmp_path):
    script = ROOT / "scripts/install-skill.sh"

    assert script.exists()
    assert script.stat().st_mode & stat.S_IXUSR

    env = os.environ.copy()
    env["CODEX_HOME"] = str(tmp_path / "codex-home")
    result = subprocess.run(
        [str(script)],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    link = tmp_path / "codex-home/skills/springboot-project-generator"
    assert result.returncode == 0, result.stderr
    assert link.is_symlink()
    assert link.resolve() == ROOT / "skills/springboot-project-generator"
    assert "springboot-project-generator" in result.stdout


def test_windows_install_script_is_documented():
    script = ROOT / "scripts/install-skill.ps1"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    content = script.read_text(encoding="utf-8")

    assert script.exists()
    assert "New-Item" in content
    assert "Junction" in content
    assert "Copy-Item" in content
    assert "CODEX_HOME" in content
    assert ".\\scripts\\install-skill.ps1" in readme


def test_console_script_entrypoint_works_without_installation():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "springboot_project_generator",
            "generate",
            "--help",
        ],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    assert result.returncode == 0, result.stderr
    assert "--project-name" in result.stdout
    assert "--config" in result.stdout


def test_generated_project_smoke_files_exist(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "springboot_project_generator",
            "generate",
            "--project-name",
            "smoke",
            "--base-package",
            "com.example.smoke",
            "--description",
            "smoke backend with product management",
            "--entity",
            "Product",
            "--output-dir",
            str(tmp_path),
            "--no-interactive",
        ],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    project_dir = tmp_path / "smoke"
    assert result.returncode == 0, result.stderr
    assert (project_dir / "pom.xml").exists()
    assert (project_dir / "smoke-server/pom.xml").exists()
    assert (
        project_dir
        / "smoke-server/src/main/java/com/example/smoke/controller/HealthController.java"
    ).exists()
    assert (project_dir / "smoke-server/src/main/resources/db/schema.sql").exists()
    assert (project_dir / "README.md").exists()


def test_skill_metadata_is_short_and_agent_prompt_matches_positioning():
    skill = (ROOT / "skills/springboot-project-generator/SKILL.md").read_text(encoding="utf-8")
    agent = (
        ROOT / "skills/springboot-project-generator/agents/openai.yaml"
    ).read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    frontmatter = skill.split("---", 2)[1]
    description_line = next(
        line for line in frontmatter.splitlines() if line.startswith("description:")
    )
    description = description_line.split(":", 1)[1].strip().strip('"')

    assert len(description) < 320
    assert "Use when" in description
    assert "workflow" not in description.lower()
    assert "可信赖" in agent
    assert "project.yaml" in agent
    assert "Spring Boot Backend Skill" in readme


def test_tests_use_explicit_utf8_for_text_file_io():
    for test_file in (ROOT / "tests").glob("test_*.py"):
        content = test_file.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in {"read_text", "write_text"}:
                continue
            keyword_names = {keyword.arg for keyword in node.keywords}
            assert "encoding" in keyword_names, test_file
