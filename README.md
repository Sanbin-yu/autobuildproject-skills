# Spring Boot Backend Skill

[![CI](https://github.com/Sanbin-yu/autobuildproject-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/Sanbin-yu/autobuildproject-skills/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

从业务描述和 `project.yaml` 生成可构建、可测试的 Maven 多模块 Spring Boot 后端项目。

这个仓库包含两部分：

- Codex Skill：负责项目问诊，把业务对象、角色、字段和技术栈整理成结构化配置。
- Python CLI：负责稳定生成 Spring Boot 项目，是可测试的生成引擎。

当前不是生产级后端生成器。v0.2 的目标是降低安装、运行和贡献门槛：让别人敢安装、敢执行示例、敢看 CI 结果；真实数据库 CRUD、完整 JWT 登录、RBAC 和增量生成会放到后续版本。

## Quick Start

克隆仓库后，直接生成一个示例项目：

```bash
python3 -m springboot_project_generator generate \
  --project-name demo \
  --base-package com.example.demo \
  --description "demo backend with product management" \
  --entity Product \
  --output-dir /tmp \
  --no-interactive
```

也可以先安装为本地可执行命令：

```bash
python -m pip install -e .
springboot-project-generator generate --help
```

验证生成物：

```bash
cd /tmp/demo
mvn test
mvn package
```

想用隔离的一次性环境，可以从 GitHub 运行：

```bash
pipx run --spec git+https://github.com/Sanbin-yu/autobuildproject-skills.git springboot-project-generator generate --help
uvx --from git+https://github.com/Sanbin-yu/autobuildproject-skills.git springboot-project-generator generate --help
```

> 当前尚未发布 PyPI 包；`pipx run` / `uvx` 使用 Git URL 运行仓库里的 CLI 入口。

## Install The Skill

macOS / Linux：

```bash
./scripts/install-skill.sh
```

Windows / PowerShell：

```powershell
.\scripts\install-skill.ps1
```

默认安装到 `~/.codex/skills/springboot-project-generator`。也可以通过 `CODEX_HOME` 指定 Codex 目录：

```bash
CODEX_HOME=/path/to/.codex ./scripts/install-skill.sh
```

```powershell
$env:CODEX_HOME="C:\Users\you\.codex"
.\scripts\install-skill.ps1
```

安装后，让 Codex 使用 `$springboot-project-generator` 创建 Spring Boot 后端项目。

## Windows / PowerShell

Windows 用户建议使用 PowerShell 安装脚本：

```powershell
.\scripts\install-skill.ps1
```

如果系统策略阻止创建符号链接，可以用管理员 PowerShell 运行，或开启 Windows Developer Mode 后重试。

## Supported Scope

- Spring Boot 3.x
- Java 21
- Maven multi-module
- Python 3.11+
- Parent project plus `<project>-common`、`<project>-pojo`、`<project>-server`
- 内存 CRUD，可健康启动，不要求首次运行就连接 MySQL、Redis 或 RabbitMQ
- MyBatis-Plus / MySQL 骨架
- Security / JWT 骨架
- Redis / RabbitMQ 配置骨架
- `project.yaml` 结构化配置：业务对象、字段、角色、技术栈开关
- 生成 `schema.sql` 数据库草稿

## Not Supported Yet

- 当前不是生产级后端生成器；生成物适合作为后端项目起点和学习/原型骨架
- 增量更新已有项目并保护用户代码
- 完整生产级 JWT 登录链路
- 真实数据库 CRUD 实现替代内存 Map
- Flyway / Liquibase 迁移
- OpenAPI / Swagger 文档
- Docker Compose 一键启动 MySQL、Redis、RabbitMQ
- 已发布的 PyPI 包

## Generated Project Shape

典型生成目录：

```text
demo
├── demo-common
│   └── src/main/java/com/example/demo
│       ├── constant
│       ├── context
│       ├── enumeration
│       ├── exception
│       ├── json
│       ├── properties
│       ├── result
│       └── utils
├── demo-pojo
│   └── src/main/java/com/example/demo
│       ├── dto
│       ├── entity
│       └── vo
├── demo-server
│   └── src/main/java/com/example/demo
│       ├── config
│       ├── controller
│       ├── handler
│       ├── interceptor
│       ├── mapper
│       └── service
├── pom.xml
└── README.md
```

## Example APIs

假设生成了 `Product`：

```text
GET    /api/health
POST   /api/products
GET    /api/products/{id}
GET    /api/products?page=1&pageSize=10&keyword=phone
PUT    /api/products
DELETE /api/products/{id}
```

默认 `app.security.enabled=false`，健康检查和 CRUD 骨架可以直接启动验证。需要更严格认证时，在配置中启用 Security/JWT 后继续完善登录链路。

## Example Generation

默认全功能项目会包含 Web、Validation、Security/JWT、MyBatis-Plus/MySQL、Redis、RabbitMQ 和测试依赖骨架：

```bash
python -m springboot_project_generator generate \
  --project-name ci-default \
  --base-package com.example.cidefault \
  --description "default backend with product management" \
  --entity Product \
  --output-dir /tmp \
  --no-interactive
```

lean 项目可以通过 `project.yaml` 关闭 Security、JWT、Redis、RabbitMQ、MySQL 和 MyBatis-Plus，只保留可启动的 Web/Validation/内存 CRUD 骨架：

```yaml
projectName: ci-lean
basePackage: com.example.cilean
description: lean backend with task management
outputDir: /tmp
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
```

结构化业务示例放在 `examples/club-project.yaml`：

```bash
python -m springboot_project_generator generate --config examples/club-project.yaml --no-interactive
cd /tmp/club
mvn package
```

仓库只提交示例配置和 README 片段，不提交完整生成物；CI 会在临时目录里重新生成并验证。

## project.yaml

最小配置：

```yaml
projectName: gym
basePackage: com.acme.gym
description: gym membership backend with member and trainer management
outputDir: ./examples
entities:
  - Member
  - Trainer
```

结构化配置：

```yaml
projectName: club
basePackage: com.acme.club
description: club backend with member and coach management
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
      - name: active
        type: Boolean
  - name: Coach
    fields:
      - name: name
        type: String
        required: true
      - name: specialty
        type: String
      - name: hourlyRate
        type: BigDecimal
```

生成：

```bash
python3 -m springboot_project_generator generate --config project.yaml --no-interactive
```

支持的常用字段类型：`String`、`Integer`、`Long`、`BigDecimal`、`LocalDateTime`、`LocalDate`、`Boolean`、`Double`。

## Codex Workflow

这个 skill 会先问诊：

- 项目类型
- 核心业务对象
- 对象字段
- 用户角色
- 数据持久化
- 外部服务
- 安全要求

然后整理 `project.yaml` 草稿，用户确认后再调用 CLI 生成项目。

## Development

运行 Python 测试：

```bash
python -m pytest
PYTHONUTF8=1 python -m pytest
```

本地复现 CI 生成物检查：

```bash
scripts/ci-smoke.sh all
scripts/ci-smoke.sh default
scripts/ci-smoke.sh lean
```

如只想检查生成结构、不跑 Maven：

```bash
CI_SMOKE_SKIP_MAVEN=1 scripts/ci-smoke.sh all
```

CI 使用 Ubuntu 和 Windows matrix，调用 `scripts/ci-smoke.sh all` 生成默认全功能项目与 lean 项目，并执行 smoke 文件检查和 `mvn package`。

## License

MIT License. See [LICENSE](LICENSE).
