---
name: springboot-project-generator
description: Use when creating or scaffolding Maven multi-module Spring Boot backend projects, common/pojo/server modules, backend dependencies, CRUD scaffolding, Java packages, pom.xml files, schema.sql, runnable starter backend, Spring Boot 项目脚手架, 多模块后端项目.
---

# Spring Boot 项目生成器

## 概览

使用仓库内置的 Python CLI 作为稳定生成引擎。先理解用户想做什么项目，再确认环境和生成选项，最后运行 CLI。

## 工作流程

1. 生成前先做简短项目问诊。不要直接跳过问诊运行 CLI，除非用户已经给出完整 `project.yaml`。
2. 问诊后先整理 project.yaml 草稿，展示给用户确认；确认后再运行生成器。
3. 使用 `java -version` 和 `mvn -version` 检测本地版本；版本会影响生成结果时，让用户确认或覆盖。
4. 在仓库根目录运行生成器。只有在必要信息已经明确时才使用 `--no-interactive`。使用 `--dry-run` 可以只展示生成计划，不写入文件。

## 项目问诊

固定覆盖这 7 项，尽量一次问清，但保持问题简洁：

1. 项目类型：例如后台管理、商城、预约系统、会员系统、内容平台。
2. 核心业务对象：1-3 个最重要的对象，例如 Member、Order、Product。
3. 对象字段：每个对象 2-6 个关键字段，标出必填、唯一、金额、时间等含义。
4. 用户角色：例如 admin、user、operator、merchant；没有就留空。
5. 数据持久化：是否需要 MySQL/MyBatis-Plus，是否只要可启动内存骨架。
6. 外部服务：是否需要 Redis、RabbitMQ，是否只是预留配置。
7. 安全要求：是否启用 Security/JWT，默认健康检查和基础 CRUD 可启动。

用户确认 `project.yaml` 草稿后再运行：

```bash
python3 -m springboot_project_generator generate --config project.yaml --no-interactive
```

结构化 `project.yaml` 示例：

```yaml
projectName: club
basePackage: com.acme.club
description: club backend with member management
outputDir: ./examples
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
```

## 默认规则

- 项目结构：Maven 父工程，加 `<project>-common`、`<project>-pojo`、`<project>-server` 三个模块。
- 依赖：Web、Validation、Security、MyBatis-Plus、MySQL、Lombok、JWT、Redis、RabbitMQ、Test。
- 业务生成范围：1-3 个核心实体，并生成 entity/dto/vo/controller/service/mapper CRUD 骨架。
- 字段级生成：如果用户提供字段，字段会进入 Entity、DTO、ListVO、DetailVO、ServiceImpl 和 `schema.sql`。
- 字段类型：优先使用 `String`、`Integer`、`Long`、`BigDecimal`、`LocalDateTime`、`LocalDate`、`Boolean`、`Double`。
- 外部服务：生成配置默认不要求首次启动时必须连接 MySQL、Redis 或 RabbitMQ。
- 技术栈开关：关闭 Security、JWT、Redis、RabbitMQ、MySQL、MyBatis-Plus 时，要同步裁剪相关依赖和生成代码。
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
