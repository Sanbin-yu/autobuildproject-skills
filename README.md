# Spring Boot Project Generator Skill

Open-source-ready Codex skill and Python CLI for generating Maven multi-module
Spring Boot backend projects.

## What It Generates

- Parent Maven project with `<project>-common`, `<project>-pojo`, and `<project>-server`
- Common backend dependencies: Web, Validation, Security, MyBatis-Plus, MySQL,
  Lombok, JWT, Redis, RabbitMQ, and Test
- Common module packages for constants, context, enums, exceptions, JSON,
  properties, result wrappers, and utilities
- POJO module packages for `entity`, `dto`, and `vo`
- Server module packages for app entrypoint, config, controller, handler,
  interceptor, mapper, service, and service implementation
- 1-3 generated business objects with basic CRUD scaffolding
- `schema.sql` and a generated project README

## CLI Usage

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

Dry run:

```bash
python3 -m springboot_project_generator generate \
  --project-name mall \
  --description "online mall backend with product, order, and customer management" \
  --dry-run \
  --no-interactive
```

## Codex Skill Usage

Copy or symlink `skills/springboot-project-generator` into your Codex skills
directory, then ask Codex to use `$springboot-project-generator` to create a
Spring Boot backend project.

The skill asks a short project diagnosis before generation, confirms local
Java/Maven versions, then calls the Python CLI.

## Development

```bash
python3 -m pytest
```

To verify generated Java output:

```bash
python3 -m springboot_project_generator generate \
  --project-name demo \
  --description "demo backend with product management" \
  --output-dir /tmp \
  --no-interactive
cd /tmp/demo
mvn test
```

