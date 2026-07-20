# v0.3 Progress

## 2026-07-20

- Read current project files, README, Skill docs, tests, and core generator implementation.
- Confirmed clean git status before editing.
- Confirmed current checkout is a normal `main` checkout, not a linked worktree.
- Confirmed local and bundled Python runtimes do not currently have `pytest` installed.
- Created persistent planning files for v0.3 implementation.
- Created a temporary test virtualenv at `/tmp/autobuildproject-v03-venv` and installed `pytest`.
- Added failing v0.3 tests for route pluralization, MyBatis-Plus CRUD generation, lean-mode preservation, docs, and version metadata.
- Verified red tests:
  - `test_generated_controller_uses_single_pluralized_route_path` fails because `Product` routes are still double-pluralized.
  - `test_default_mybatis_plus_service_uses_mapper_crud` fails because ServiceImpl still uses in-memory storage.
  - v0.3 docs/version tests fail because metadata/docs still describe v0.2 behavior.
- Implemented route path fix, PascalCase-preserving naming, database-backed ServiceImpl rendering, H2 test datasource generation, and v0.3 docs/version updates.
- Verified focused tests:
  - `tests/test_generator.py` passed: 12 tests.
  - v0.3 docs/version focused tests passed: 2 tests.
- Verified full Python test suite: 33 passed.
- Generated `/tmp/codex-v03-default` successfully.
- Error: attempted lean smoke generation with `--config /tmp/nonexistent`; CLI correctly failed because the config file did not exist. Next attempt will use a real temporary config.
- Generated `/tmp/codex-v03-lean` successfully with a temporary config.
- Maven smoke attempted for default and lean generated projects. Both compiled and reached Spring context tests, then failed because Mockito/Byte Buddy could not self-attach on the local JDK.
- Added failing test for generated POM Mockito exclusions, then updated root POM templates to exclude `mockito-core` and `mockito-junit-jupiter`.
- Re-ran full Python test suite: 33 passed.
- Ran `scripts/ci-smoke.sh all`: generated default and lean projects, ran Maven package for both, and both builds succeeded.
- Final verification:
  - `/tmp/autobuildproject-v03-venv/bin/python -m pytest -q`: 33 passed.
  - `scripts/ci-smoke.sh all`: default and lean generated projects both built successfully with Maven.
  - `git diff --check`: passed with no whitespace errors.
