# Examples

这个目录只提交示例配置和说明，不会提交完整生成物。这样仓库保持轻量，CI 和本地验证都可以从配置重新生成项目。

## Club Project

`club-project.yaml` 展示结构化业务输入：角色、技术栈开关、实体和字段。

生成示例项目：

```bash
python -m springboot_project_generator generate --config examples/club-project.yaml --no-interactive
```

默认会生成到 `/tmp/club`。验证：

```bash
cd /tmp/club
mvn package
```

生成物会包含：

- Maven 父工程和 `club-common`、`club-pojo`、`club-server`
- `HealthController.java`
- `Member` / `Coach` 的 entity、dto、vo、controller、service、mapper
- `club-server/src/main/resources/db/schema.sql`
- 生成项目自己的 `README.md`
