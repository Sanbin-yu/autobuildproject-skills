import subprocess
import sys


def test_cli_generate_non_interactive_project(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "springboot_project_generator",
            "generate",
            "--project-name",
            "gym",
            "--base-package",
            "com.acme.gym",
            "--description",
            "gym membership backend with member and trainer management",
            "--entity",
            "Member",
            "--entity",
            "Trainer",
            "--output-dir",
            str(tmp_path),
            "--java-version",
            "21",
            "--maven-version",
            "3.9.9",
            "--no-interactive",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Created Spring Boot project" in result.stdout
    assert (tmp_path / "gym/gym-common/pom.xml").exists()
    assert (
        tmp_path / "gym/gym-server/src/main/java/com/acme/gym/controller/MemberController.java"
    ).exists()


def test_cli_dry_run_prints_plan_without_creating_files(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "springboot_project_generator",
            "generate",
            "--project-name",
            "library",
            "--description",
            "library backend",
            "--output-dir",
            str(tmp_path),
            "--dry-run",
            "--no-interactive",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Project plan" in result.stdout
    assert not (tmp_path / "library").exists()

