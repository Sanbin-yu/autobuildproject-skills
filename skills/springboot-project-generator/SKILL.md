---
name: springboot-project-generator
description: Use when creating or scaffolding Maven multi-module Spring Boot backend projects, common/pojo/server modules, backend dependencies, CRUD scaffolding, Java packages, pom.xml files, schema.sql, runnable starter backend, Spring Boot 项目脚手架, 多模块后端项目.
---

# Spring Boot 项目生成器

## 概览

使用仓库内置的 Python CLI 作为稳定生成引擎。先理解用户想做什么项目，再确认环境和生成选项，最后运行 CLI。

## 工作流程

1. 生成前先做简短项目问诊：
   - 项目名称
   - 基础包名，或者默认使用 `com.example.<project>`
   - 项目方向和目标用户
   - 1-3 个核心业务对象
   - 角色权限或安全需求
   - 数据库、缓存、消息队列需求
   - 输出目录
2. 使用 `java -version` 和 `mvn -version` 检测本地版本；版本会影响生成结果时，让用户确认或覆盖。
3. 在仓库根目录运行生成器：

```bash
python3 -m springboot_project_generator generate \
  --project-name <name> \
  --base-package <package> \
  --description "<project direction>" \
  --entity <EntityOne> \
  --entity <EntityTwo> \
  --output-dir <directory>
```

只有在必要信息已经明确时才使用 `--no-interactive`。使用 `--dry-run` 可以只展示生成计划，不写入文件。

复杂项目优先生成 `project.yaml`，再运行：

```bash
python3 -m springboot_project_generator generate --config project.yaml --no-interactive
```

## 默认规则

- 项目结构：Maven 父工程，加 `<project>-common`、`<project>-pojo`、`<project>-server` 三个模块。
- 依赖：Web、Validation、Security、MyBatis-Plus、MySQL、Lombok、JWT、Redis、RabbitMQ、Test。
- 业务生成范围：1-3 个核心实体，并生成 entity/dto/vo/controller/service/mapper CRUD 骨架。
- 外部服务：生成配置默认不要求首次启动时必须连接 MySQL、Redis 或 RabbitMQ。
- 已存在目标目录：不要覆盖；让用户选择新的输出目录或项目名。
- 模板：Maven、项目 README、application.yml 已外置在 `templates/`，修改模板优先改模板文件。

## 验证

生成后运行：

```bash
cd <generated-project>
mvn test
mvn package
```

如果 Maven 因依赖下载失败而报错，需要把网络或依赖仓库问题和生成器正确性分开说明。

## 常见错误

| 错误 | 处理方式 |
| --- | --- |
| 还没问清用户要做什么项目就开始生成 | 先做简短项目问诊 |
| 手写文件而不是调用 CLI | 调用仓库内置生成器 |
| 一次猜太多实体 | v1 保持 1-3 个核心业务对象 |
| 覆盖已有项目 | 停下来，让用户换目标目录或项目名 |
| 把 `schema.sql` 当成最终数据库设计 | 明确说明它只是可修改的初稿 |
