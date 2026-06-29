from pathlib import Path

import pytest

from springboot_project_generator.core import (
    ProjectOptions,
    derive_names,
    generate_project,
    load_project_config,
)


def test_derive_names_normalizes_project_and_package():
    names = derive_names("Gym Membership", None)

    assert names.project_name == "gym-membership"
    assert names.project_class_name == "GymMembership"
    assert names.base_package == "com.example.gymmembership"
    assert names.common_module == "gym-membership-common"
    assert names.pojo_module == "gym-membership-pojo"
    assert names.server_module == "gym-membership-server"
    assert names.package_path == Path("com/example/gymmembership")


def test_generate_project_creates_multimodule_layout(tmp_path):
    options = ProjectOptions(
        project_name="mall",
        base_package="com.acme.mall",
        description="online mall backend with product, order, and customer management",
        output_dir=tmp_path,
        entities=["Product", "Order", "Customer"],
        java_version="21",
        maven_version="3.9.9",
    )

    project_dir = generate_project(options)

    assert project_dir == tmp_path / "mall"
    assert (project_dir / "pom.xml").exists()
    assert (project_dir / "mall-common/pom.xml").exists()
    assert (project_dir / "mall-pojo/pom.xml").exists()
    assert (project_dir / "mall-server/pom.xml").exists()
    assert (
        project_dir
        / "mall-server/src/main/java/com/acme/mall/MallApplication.java"
    ).exists()
    assert (
        project_dir
        / "mall-common/src/main/java/com/acme/mall/result/Result.java"
    ).exists()
    assert (
        project_dir
        / "mall-pojo/src/main/java/com/acme/mall/entity/Product.java"
    ).exists()
    assert (
        project_dir
        / "mall-server/src/main/java/com/acme/mall/controller/ProductController.java"
    ).exists()
    assert (
        project_dir
        / "mall-server/src/main/resources/db/schema.sql"
    ).exists()
    assert (project_dir / "README.md").exists()


def test_rendered_files_contain_expected_dependencies_and_names(tmp_path):
    options = ProjectOptions(
        project_name="order-hub",
        base_package="com.example.orders",
        description="order management backend",
        output_dir=tmp_path,
        entities=["Order"],
        java_version="17",
        maven_version="3.9.9",
    )

    project_dir = generate_project(options)

    root_pom = (project_dir / "pom.xml").read_text()
    app = (
        project_dir
        / "order-hub-server/src/main/java/com/example/orders/OrderHubApplication.java"
    ).read_text()
    controller = (
        project_dir
        / "order-hub-server/src/main/java/com/example/orders/controller/OrderController.java"
    ).read_text()
    readme = (project_dir / "README.md").read_text()

    assert "<artifactId>spring-boot-starter-web</artifactId>" in root_pom
    assert "<artifactId>mybatis-plus-spring-boot3-starter</artifactId>" in root_pom
    assert "<artifactId>mysql-connector-j</artifactId>" in root_pom
    assert "<artifactId>spring-boot-starter-data-redis</artifactId>" in root_pom
    assert "<artifactId>spring-boot-starter-amqp</artifactId>" in root_pom
    assert "package com.example.orders;" in app
    assert "class OrderController" in controller
    assert "order-hub-common" in readme
    assert "mvn test" in readme


def test_generate_project_refuses_existing_target_directory(tmp_path):
    target = tmp_path / "catalog"
    target.mkdir()
    options = ProjectOptions(
        project_name="catalog",
        base_package="com.example.catalog",
        description="catalog backend",
        output_dir=tmp_path,
        entities=["CatalogItem"],
    )

    with pytest.raises(FileExistsError):
        generate_project(options)


def test_load_project_config_supports_yaml_fields(tmp_path):
    config = tmp_path / "project.yaml"
    config.write_text(
        """
projectName: library-system
basePackage: com.acme.library
description: library backend with book and reader management
outputDir: generated
javaVersion: "21"
mavenVersion: 3.9.9
springBootVersion: 3.3.5
entities:
  - Book
  - Reader
""".strip()
    )

    options = load_project_config(config)

    assert options.project_name == "library-system"
    assert options.base_package == "com.acme.library"
    assert options.output_dir == tmp_path / "generated"
    assert options.entities == ["Book", "Reader"]
    assert options.java_version == "21"
    assert options.maven_version == "3.9.9"


def test_generate_project_from_config_creates_expected_entities(tmp_path):
    config = tmp_path / "project.yaml"
    config.write_text(
        """
projectName: library
basePackage: com.acme.library
description: library backend
outputDir: .
entities:
  - Book
  - BorrowRecord
""".strip()
    )

    options = load_project_config(config)
    project_dir = generate_project(options)

    assert (
        project_dir
        / "library-pojo/src/main/java/com/acme/library/entity/BorrowRecord.java"
    ).exists()
    assert (
        project_dir
        / "library-server/src/main/java/com/acme/library/controller/BorrowRecordController.java"
    ).exists()
