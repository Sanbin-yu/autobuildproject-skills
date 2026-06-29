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


def test_cli_generate_from_project_yaml(tmp_path):
    config = tmp_path / "project.yaml"
    config.write_text(
        """
projectName: clinic
basePackage: com.acme.clinic
description: clinic backend with patient management
outputDir: .
entities:
  - Patient
  - Appointment
""".strip()
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "springboot_project_generator",
            "generate",
            "--config",
            str(config),
            "--no-interactive",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "clinic/clinic-server/pom.xml").exists()
    assert (
        tmp_path
        / "clinic/clinic-server/src/main/java/com/acme/clinic/controller/PatientController.java"
    ).exists()


def test_cli_config_versions_are_not_overwritten_by_cli_defaults(tmp_path):
    config = tmp_path / "project.yaml"
    config.write_text(
        """
projectName: versioned
basePackage: com.acme.versioned
description: versioned backend
outputDir: .
springBootVersion: 3.2.6
mybatisPlusVersion: 3.5.5
jwtVersion: 0.12.5
entities:
  - VersionedItem
""".strip()
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "springboot_project_generator",
            "generate",
            "--config",
            str(config),
            "--no-interactive",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    assert result.returncode == 0, result.stderr
    pom = (tmp_path / "versioned/pom.xml").read_text()
    assert "<version>3.2.6</version>" in pom
    assert "<mybatis-plus.version>3.5.5</mybatis-plus.version>" in pom
    assert "<jjwt.version>0.12.5</jjwt.version>" in pom
