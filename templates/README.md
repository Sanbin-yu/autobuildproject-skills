# 模板

这个目录存放已经外置的生成模板。

- `maven/root-pom.xml.tpl`：Maven 父工程模板
- `project/README.md.tpl`：生成项目 README 模板
- `resources/application.yml.tpl`：server 模块 application.yml 模板

模板使用 `__TOKEN__` 占位符，由 Python 生成器替换。复杂 Java 类模板后续也可以逐步从 `core.py` 拆到这里。
