import argparse
import sys
from pathlib import Path

from .core import (
    ProjectOptions,
    describe_plan,
    detect_java_version,
    detect_maven_version,
    generate_project,
    infer_entities,
    load_project_config,
)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="springboot-project-generator",
        description="Generate a Maven multi-module Spring Boot backend project.",
    )
    subparsers = parser.add_subparsers(dest="command")

    generate = subparsers.add_parser("generate", help="Generate a new project")
    generate.add_argument("--config", help="Path to a project.yaml config file")
    generate.add_argument("--project-name")
    generate.add_argument("--base-package")
    generate.add_argument("--description")
    generate.add_argument("--output-dir", default=".")
    generate.add_argument("--entity", action="append", default=[])
    generate.add_argument("--java-version")
    generate.add_argument("--maven-version")
    generate.add_argument("--spring-boot-version")
    generate.add_argument("--mybatis-plus-version")
    generate.add_argument("--jwt-version")
    generate.add_argument("--dry-run", action="store_true")
    generate.add_argument("--no-interactive", action="store_true")

    return parser


def _confirm(value, label, no_interactive):
    if no_interactive:
        return value
    answer = input("%s [%s]: " % (label, value)).strip()
    return answer or value


def build_options(args):
    if args.config:
        options = load_project_config(args.config)
        return merge_config_options(options, args)

    if not args.project_name:
        raise ValueError("--project-name is required when --config is not provided")
    if not args.description:
        raise ValueError("--description is required when --config is not provided")

    java_version = args.java_version or detect_java_version() or "21"
    maven_version = args.maven_version or detect_maven_version() or "3.9"

    java_version = _confirm(java_version, "Java version", args.no_interactive)
    maven_version = _confirm(maven_version, "Maven version", args.no_interactive)

    entities = args.entity or infer_entities(args.description)

    return ProjectOptions(
        project_name=args.project_name,
        base_package=args.base_package,
        description=args.description,
        output_dir=Path(args.output_dir),
        entities=entities,
        java_version=java_version,
        maven_version=maven_version,
        spring_boot_version=args.spring_boot_version or "3.3.5",
        mybatis_plus_version=args.mybatis_plus_version or "3.5.7",
        jwt_version=args.jwt_version or "0.12.6",
    )


def merge_config_options(options, args):
    java_version = args.java_version or options.java_version
    maven_version = args.maven_version or options.maven_version
    if not args.no_interactive:
        java_version = _confirm(java_version, "Java version", args.no_interactive)
        maven_version = _confirm(maven_version, "Maven version", args.no_interactive)
    return ProjectOptions(
        project_name=args.project_name or options.project_name,
        base_package=args.base_package or options.base_package,
        description=args.description or options.description,
        output_dir=Path(args.output_dir) if args.output_dir != "." else options.output_dir,
        entities=args.entity or options.entities,
        roles=options.roles,
        features=options.features,
        java_version=java_version,
        maven_version=maven_version,
        spring_boot_version=args.spring_boot_version or options.spring_boot_version,
        mybatis_plus_version=args.mybatis_plus_version or options.mybatis_plus_version,
        jwt_version=args.jwt_version or options.jwt_version,
    )


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "generate":
        parser.print_help()
        return 2

    try:
        options = build_options(args)
        if args.dry_run:
            print("Project plan")
            print(describe_plan(options))
            return 0

        project_dir = generate_project(options)
        print("Created Spring Boot project at %s" % project_dir)
        print("Next steps:")
        print("  cd %s" % project_dir)
        print("  mvn test")
        return 0
    except Exception as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
