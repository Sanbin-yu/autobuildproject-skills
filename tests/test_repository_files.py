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
    assert "project.yaml" in readme


def test_repository_contains_external_templates():
    template_files = [
        ROOT / "templates/maven/root-pom.xml.tpl",
        ROOT / "templates/project/README.md.tpl",
        ROOT / "templates/resources/application.yml.tpl",
    ]

    for template_file in template_files:
        assert template_file.exists(), template_file
        assert "__PROJECT_NAME__" in template_file.read_text()


def test_github_actions_workflow_runs_python_and_generated_project_checks():
    workflow = ROOT / ".github/workflows/ci.yml"

    content = workflow.read_text()

    assert "python3 -m pytest" in content
    assert "springboot_project_generator generate" in content
    assert "mvn package" in content
