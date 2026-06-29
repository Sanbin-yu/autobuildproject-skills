---
name: springboot-project-generator
description: Use when creating or scaffolding Maven multi-module Spring Boot backend projects, especially when the user wants common/pojo/server modules, backend dependencies, CRUD scaffolding, Java packages, pom.xml files, schema.sql, or a runnable starter backend generated from a project idea.
---

# Spring Boot Project Generator

## Overview

Use the bundled Python CLI as the generation engine. First understand the user's project, then confirm environment and generation options, then run the CLI.

## Workflow

1. Ask a concise project diagnosis before generating:
   - project name
   - base package, or use `com.example.<project>`
   - project direction and target users
   - 1-3 core business objects
   - roles or security expectations
   - database/cache/message queue needs
   - output directory
2. Detect local versions with `java -version` and `mvn -version`; ask the user to confirm or override when the versions matter.
3. Run the generator from the repository root:

```bash
python3 -m springboot_project_generator generate \
  --project-name <name> \
  --base-package <package> \
  --description "<project direction>" \
  --entity <EntityOne> \
  --entity <EntityTwo> \
  --output-dir <directory>
```

Use `--no-interactive` only after the needed answers are known. Use `--dry-run` to show the plan without writing files.

## Defaults

- Project shape: parent Maven project plus `<project>-common`, `<project>-pojo`, `<project>-server`.
- Dependencies: Web, Validation, Security, MyBatis-Plus, MySQL, Lombok, JWT, Redis, RabbitMQ, Test.
- Generated business scope: 1-3 core entities with entity/dto/vo/controller/service/mapper CRUD scaffolding.
- External services: generated config defaults should not require live MySQL, Redis, or RabbitMQ for first startup.
- Existing target directory: do not overwrite; choose a new output directory or project name.

## Verification

After generation, run:

```bash
cd <generated-project>
mvn test
```

If Maven fails because dependencies cannot be downloaded, report the network/dependency issue separately from generator correctness.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Generating before asking what project the user wants | Ask the short diagnosis first |
| Writing files by hand instead of using the CLI | Call the bundled generator |
| Guessing too many entities | Keep v1 to 1-3 core business objects |
| Overwriting an existing project | Stop and ask for a new target |
| Treating `schema.sql` as final design | Present it as a modifiable draft |

