# Spring Boot 项目生成器 Skill

这是一个面向 Codex 的 skill，同时提供 Python CLI，用于快速生成 Maven 多模块 Spring Boot 后端项目。

## 可以生成什么

- Maven 父工程，以及 `<project>-common`、`<project>-pojo`、`<project>-server` 三个模块
- 常用后端依赖：Web、Validation、Security、MyBatis-Plus、MySQL、Lombok、JWT、Redis、RabbitMQ、Test
- common 模块：constant、context、enumeration、exception、json、properties、result、utils
- pojo 模块：`entity`、`dto`、`vo`
- server 模块：启动类、config、controller、handler、interceptor、mapper、service、service.impl
- 根据项目方向生成 1-3 个核心业务对象，并生成基础 CRUD 骨架
- `schema.sql` 数据库初稿和生成项目自己的 README

## CLI 使用方式

```bash
python3 -m springboot_project_generator generate \
  --project-name gym \
  --base-package com.acme.gym \
  --description "gym membership backend with member and trainer management" \
  --entity Member \
  --entity Trainer \
  --output-dir ./examples \
  --no-interactive
```

也可以使用 `project.yaml`：

```yaml
projectName: gym
basePackage: com.acme.gym
description: gym membership backend with member and trainer management
outputDir: ./examples
javaVersion: "21"
mavenVersion: 3.9.9
entities:
  - Member
  - Trainer
```

```bash
python3 -m springboot_project_generator generate --config project.yaml --no-interactive
```

只查看生成计划，不写入文件：

```bash
python3 -m springboot_project_generator generate \
  --project-name mall \
  --description "online mall backend with product, order, and customer management" \
  --dry-run \
  --no-interactive
```

## Codex Skill 使用方式

把 `skills/springboot-project-generator` 复制或软链接到你的 Codex skills 目录，然后让 Codex 使用 `$springboot-project-generator` 创建 Spring Boot 后端项目。

这个 skill 会先询问项目名称、包名、业务方向、核心实体、角色权限、数据库/缓存/消息队列需求等信息，再确认本地 Java/Maven 版本，最后调用 Python CLI 生成项目。

## 开发与测试

```bash
python3 -m pytest
```

仓库已包含 GitHub Actions：每次 push 或 PR 会运行 Python 测试、生成示例项目，并对示例项目执行 `mvn package`。

验证生成出来的 Java 项目：

```bash
python3 -m springboot_project_generator generate \
  --project-name demo \
  --description "demo backend with product management" \
  --output-dir /tmp \
  --no-interactive
cd /tmp/demo
mvn test
mvn package
```
