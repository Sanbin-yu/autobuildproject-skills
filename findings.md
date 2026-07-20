# v0.3 Findings

## Project Context

- The repository is a Python package named `springboot-project-generator` at version `0.2.0`.
- The CLI entry point is `springboot_project_generator.cli:main`.
- `springboot_project_generator/core.py` currently contains naming, config parsing, Java rendering, templates, schema rendering, and service implementation rendering.
- `render_service_impl` always emits an in-memory `ConcurrentHashMap` service.
- `render_mapper` emits a MyBatis-Plus `BaseMapper` only when `features.mybatis_plus` is enabled.
- `render_controller` currently computes controller paths from `pluralize(table_name(entity).replace("_", "-"))`, which double-pluralizes entities such as `Product` into `productses`.

## Desired v0.3 Behavior

- Full/default feature projects should generate ServiceImpl classes that call MyBatis-Plus mapper methods: `insert`, `selectById`, `selectPage`, `updateById`, and `deleteById`.
- Lean projects should keep the existing in-memory implementation and avoid MyBatis imports.
- `Product` should generate `/api/products`; snake-case table names such as `BorrowRecord` should become kebab-case paths like `/api/borrow-records`.
- Generated Maven smoke compiled default and lean projects, then both failed during test callbacks because `spring-boot-starter-test` pulled Mockito 5 and Byte Buddy could not self-attach on the local Homebrew JDK 21. The generated context tests do not use mocks, so excluding Mockito from the generated starter-test dependency is the minimal fix.
- README and Skill docs should move real database CRUD out of "not supported yet" and keep JWT/RBAC as future work.
