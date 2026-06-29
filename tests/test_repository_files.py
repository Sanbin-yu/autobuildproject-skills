from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_skill_metadata_exists_and_mentions_diagnosis():
    skill = ROOT / "skills/springboot-project-generator/SKILL.md"

    content = skill.read_text()

    assert "name: springboot-project-generator" in content
    assert "项目问诊" in content
    assert "python3 -m springboot_project_generator generate" in content


def test_repository_readme_documents_cli_and_skill_usage():
    readme = (ROOT / "README.md").read_text()

    assert "python3 -m springboot_project_generator generate" in readme
    assert "$springboot-project-generator" in readme
    assert "mvn test" in readme
