# v0.3 Spring Boot Generator Plan

## Goal
Ship v0.3 by fixing controller route pluralization, generating real MyBatis-Plus/MySQL CRUD when database features are enabled, preserving lean in-memory CRUD when database features are disabled, and updating documentation/tests.

## Phases

| Phase | Status | Notes |
| --- | --- | --- |
| Context and design | complete | Scope approved by user on 2026-07-20. |
| Failing tests | complete | Added route, DB CRUD, lean-mode, docs/version, and Mockito-exclusion tests. |
| Implementation | complete | Updated generator renderers, POM templates, docs, and metadata. |
| Verification | complete | Python tests and CI smoke generation/Maven package passed. |

## Decisions

- v0.3 does not include JWT login or RBAC; those remain future work.
- Default/full-feature projects should use MyBatis-Plus service implementation backed by mapper calls.
- Lean projects with `mysql: false` or `mybatisPlus: false` should keep the current in-memory implementation.
- DB-enabled generated apps use H2 for `mvn test`; running the server in database mode requires configuring a MySQL datasource.

## Errors Encountered

| Error | Attempt | Resolution |
| --- | --- | --- |
| `python3 -m pytest` missing pytest | Baseline check | Use tests as TDD artifacts; request/install pytest only if needed for final verification. |
| Generated Maven smoke failed on Mockito Byte Buddy self-attach | `mvn package` on generated default and lean projects | Excluded Mockito from generated `spring-boot-starter-test` dependency because generated context tests do not use mocks. |
