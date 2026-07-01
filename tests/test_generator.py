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

    root_pom = (project_dir / "pom.xml").read_text(encoding="utf-8")
    app = (
        project_dir
        / "order-hub-server/src/main/java/com/example/orders/OrderHubApplication.java"
    ).read_text(encoding="utf-8")
    controller = (
        project_dir
        / "order-hub-server/src/main/java/com/example/orders/controller/OrderController.java"
    ).read_text(encoding="utf-8")
    readme = (project_dir / "README.md").read_text(encoding="utf-8")

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
""".strip(),
        encoding="utf-8",
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
""".strip(),
        encoding="utf-8",
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


def test_load_project_config_supports_structured_entities_features_and_roles(tmp_path):
    config = tmp_path / "project.yaml"
    config.write_text(
        """
projectName: club
basePackage: com.acme.club
description: club backend with member management
outputDir: .
roles:
  - admin
  - member
features:
  security: true
  jwt: true
  redis: false
  rabbitmq: false
  mysql: true
  mybatisPlus: true
entities:
  - name: Member
    fields:
      - name: phone
        type: String
        required: true
        unique: true
      - name: balance
        type: BigDecimal
      - name: joinedAt
        type: LocalDateTime
      - name: active
        type: Boolean
""".strip(),
        encoding="utf-8",
    )

    options = load_project_config(config)

    assert options.roles == ["admin", "member"]
    assert options.features.security is True
    assert options.features.redis is False
    assert options.features.rabbitmq is False
    assert options.features.mybatis_plus is True
    assert options.entities[0].name == "Member"
    assert options.entities[0].fields[0].name == "phone"
    assert options.entities[0].fields[0].required is True
    assert options.entities[0].fields[0].unique is True
    assert options.entities[0].fields[1].java_type == "BigDecimal"


def test_structured_entity_fields_drive_java_dto_vo_service_and_schema(tmp_path):
    config = tmp_path / "project.yaml"
    config.write_text(
        """
projectName: club
basePackage: com.acme.club
description: club backend with member management
outputDir: .
entities:
  - name: Member
    fields:
      - name: phone
        type: String
        required: true
        unique: true
      - name: balance
        type: BigDecimal
      - name: joinedAt
        type: LocalDateTime
      - name: active
        type: Boolean
""".strip(),
        encoding="utf-8",
    )

    project_dir = generate_project(load_project_config(config))

    entity = (
        project_dir / "club-pojo/src/main/java/com/acme/club/entity/Member.java"
    ).read_text(encoding="utf-8")
    create_dto = (
        project_dir / "club-pojo/src/main/java/com/acme/club/dto/MemberCreateDTO.java"
    ).read_text(encoding="utf-8")
    common_dto = (
        project_dir / "club-pojo/src/main/java/com/acme/club/dto/MemberDTO.java"
    ).read_text(encoding="utf-8")
    list_vo = (
        project_dir / "club-pojo/src/main/java/com/acme/club/vo/MemberListVO.java"
    ).read_text(encoding="utf-8")
    detail_vo = (
        project_dir / "club-pojo/src/main/java/com/acme/club/vo/MemberDetailVO.java"
    ).read_text(encoding="utf-8")
    controller = (
        project_dir
        / "club-server/src/main/java/com/acme/club/controller/MemberController.java"
    ).read_text(encoding="utf-8")
    service_impl = (
        project_dir
        / "club-server/src/main/java/com/acme/club/service/impl/MemberServiceImpl.java"
    ).read_text(encoding="utf-8")
    schema = (project_dir / "club-server/src/main/resources/db/schema.sql").read_text(encoding="utf-8")

    assert "import java.math.BigDecimal;" in entity
    assert "private String phone;" in entity
    assert "private BigDecimal balance;" in entity
    assert "private LocalDateTime joinedAt;" in entity
    assert "private Boolean active;" in entity
    assert "@NotBlank" in create_dto
    assert "private String phone;" in create_dto
    assert "public class MemberDTO" in common_dto
    assert "public class MemberListVO" in list_vo
    assert "public class MemberDetailVO" in detail_vo
    assert "Result<MemberDetailVO>" in controller
    assert "PageResult<MemberListVO>" in controller
    assert ".phone(dto.getPhone())" in service_impl
    assert "existing.setBalance(dto.getBalance());" in service_impl
    assert ".phone(item.getPhone())" in service_impl
    assert "phone VARCHAR(255) NOT NULL" in schema
    assert "balance DECIMAL(18, 2)" in schema
    assert "joined_at DATETIME" in schema
    assert "active TINYINT(1)" in schema
    assert "UNIQUE KEY uk_members_phone (phone)" in schema


def test_feature_toggles_remove_dependencies_and_matching_java_code(tmp_path):
    config = tmp_path / "project.yaml"
    config.write_text(
        """
projectName: lean
basePackage: com.acme.lean
description: lean backend
outputDir: .
features:
  security: false
  jwt: false
  redis: false
  rabbitmq: false
  mysql: false
  mybatisPlus: false
entities:
  - name: Task
    fields:
      - name: title
        type: String
        required: true
""".strip(),
        encoding="utf-8",
    )

    project_dir = generate_project(load_project_config(config))

    pom = (project_dir / "pom.xml").read_text(encoding="utf-8")
    entity = (
        project_dir / "lean-pojo/src/main/java/com/acme/lean/entity/Task.java"
    ).read_text(encoding="utf-8")
    mapper = (
        project_dir / "lean-server/src/main/java/com/acme/lean/mapper/TaskMapper.java"
    ).read_text(encoding="utf-8")

    assert "spring-boot-starter-security" not in pom
    assert "mybatis-plus-spring-boot3-starter" not in pom
    assert "mysql-connector-j" not in pom
    assert "spring-boot-starter-data-redis" not in pom
    assert "spring-boot-starter-amqp" not in pom
    assert "jjwt-api" not in pom
    assert "TableName" not in entity
    assert "TableId" not in entity
    assert "BaseMapper" not in mapper
    assert "org.apache.ibatis.annotations.Mapper" not in mapper
    assert not (
        project_dir / "lean-server/src/main/java/com/acme/lean/config/SecurityConfig.java"
    ).exists()


def test_roles_generate_permission_skeleton_and_readme_notes(tmp_path):
    config = tmp_path / "project.yaml"
    config.write_text(
        """
projectName: club
basePackage: com.acme.club
description: club backend with member management
outputDir: .
roles:
  - admin
  - member
entities:
  - name: Member
    fields:
      - name: phone
        type: String
        required: true
""".strip(),
        encoding="utf-8",
    )

    project_dir = generate_project(load_project_config(config))

    role_constant = (
        project_dir / "club-common/src/main/java/com/acme/club/constant/RoleConstant.java"
    ).read_text(encoding="utf-8")
    permission_constant = (
        project_dir
        / "club-common/src/main/java/com/acme/club/constant/PermissionConstant.java"
    ).read_text(encoding="utf-8")
    auth_context = (
        project_dir / "club-common/src/main/java/com/acme/club/context/AuthContext.java"
    ).read_text(encoding="utf-8")
    readme = (project_dir / "README.md").read_text(encoding="utf-8")

    assert 'public static final String ADMIN = "admin";' in role_constant
    assert 'public static final String MEMBER = "member";' in role_constant
    assert 'public static final String MEMBER_CREATE = "member:create";' in permission_constant
    assert 'public static final String MEMBER_PAGE = "member:page";' in permission_constant
    assert "private static final ThreadLocal<String> CURRENT_ROLE" in auth_context
    assert "- `admin`" in readme
    assert "- `member`" in readme
