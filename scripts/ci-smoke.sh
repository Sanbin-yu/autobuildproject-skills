#!/usr/bin/env sh
set -eu

usage() {
  echo "Usage: scripts/ci-smoke.sh [default|lean|all]"
  echo
  echo "Environment:"
  echo "  CI_SMOKE_OUTPUT_DIR  Directory for generated projects. Default: /tmp"
  echo "  CI_SMOKE_SKIP_MAVEN  Set to 1 to skip mvn package. Default: 0"
  echo "  PYTHON_BIN           Python command to use. Default: python3, then python"
  echo "  MAVEN_BIN            Maven command to use for mvn package. Default: mvn"
}

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
MODE="${1:-all}"
OUTPUT_DIR="${CI_SMOKE_OUTPUT_DIR:-/tmp}"
SKIP_MAVEN="${CI_SMOKE_SKIP_MAVEN:-0}"
PYTHON_BIN="${PYTHON_BIN:-}"
MAVEN_BIN="${MAVEN_BIN:-}"

if [ -z "$PYTHON_BIN" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Unable to find python3 or python. Set PYTHON_BIN=/path/to/python." >&2
    exit 127
  fi
fi

if [ "$SKIP_MAVEN" != "1" ] && [ -z "$MAVEN_BIN" ]; then
  if command -v mvn >/dev/null 2>&1; then
    MAVEN_BIN="mvn"
  elif [ -x "/opt/homebrew/bin/mvn" ]; then
    MAVEN_BIN="/opt/homebrew/bin/mvn"
  elif [ -x "/usr/local/bin/mvn" ]; then
    MAVEN_BIN="/usr/local/bin/mvn"
  else
    echo "Unable to find mvn. Set MAVEN_BIN=/path/to/mvn or CI_SMOKE_SKIP_MAVEN=1." >&2
    exit 127
  fi
fi

case "$MODE" in
  default|lean|all|help|--help|-h) ;;
  *)
    usage >&2
    exit 2
    ;;
esac

if [ "$MODE" = "help" ] || [ "$MODE" = "--help" ] || [ "$MODE" = "-h" ]; then
  usage
  exit 0
fi

run_maven_package() {
  project_dir="$1"
  if [ "$SKIP_MAVEN" = "1" ]; then
    echo "Skipping mvn package for $project_dir because CI_SMOKE_SKIP_MAVEN=1"
    return 0
  fi
  (cd "$project_dir" && "$MAVEN_BIN" package)
}

assert_file() {
  path="$1"
  if [ ! -f "$path" ]; then
    echo "Missing expected file: $path" >&2
    exit 1
  fi
}

generate_default() {
  project_dir="$OUTPUT_DIR/ci-default"
  rm -rf "$project_dir"

  "$PYTHON_BIN" -m springboot_project_generator generate \
    --project-name ci-default \
    --base-package com.example.cidefault \
    --description "default backend with product management" \
    --entity Product \
    --output-dir "$OUTPUT_DIR" \
    --java-version 21 \
    --maven-version 3.9.9 \
    --no-interactive

  assert_file "$project_dir/pom.xml"
  assert_file "$project_dir/ci-default-server/pom.xml"
  assert_file "$project_dir/ci-default-server/src/main/java/com/example/cidefault/controller/HealthController.java"
  assert_file "$project_dir/ci-default-server/src/main/resources/db/schema.sql"
  assert_file "$project_dir/README.md"

  run_maven_package "$project_dir"
}

generate_lean() {
  project_dir="$OUTPUT_DIR/ci-lean"
  config_dir="$OUTPUT_DIR/ci-smoke-configs"
  config_file="$config_dir/ci-lean.yaml"
  rm -rf "$project_dir"
  mkdir -p "$config_dir"

  "$PYTHON_BIN" - "$OUTPUT_DIR" "$config_file" <<'PY'
import sys
from pathlib import Path

output_dir = sys.argv[1]
config_file = Path(sys.argv[2])
config_file.write_text(
    f"""
projectName: ci-lean
basePackage: com.example.cilean
description: lean backend with task management
outputDir: {output_dir}
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
""".strip()
    + "\n",
    encoding="utf-8",
)
PY

  "$PYTHON_BIN" -m springboot_project_generator generate --config "$config_file" --no-interactive

  assert_file "$project_dir/pom.xml"
  assert_file "$project_dir/ci-lean-server/pom.xml"
  assert_file "$project_dir/ci-lean-server/src/main/java/com/example/cilean/controller/HealthController.java"
  assert_file "$project_dir/ci-lean-server/src/main/resources/db/schema.sql"
  assert_file "$project_dir/README.md"

  run_maven_package "$project_dir"
}

case "$MODE" in
  default)
    generate_default
    ;;
  lean)
    generate_lean
    ;;
  all)
    generate_default
    generate_lean
    ;;
esac
