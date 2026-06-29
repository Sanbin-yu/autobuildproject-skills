#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
SKILL_NAME="springboot-project-generator"
SOURCE_DIR="$REPO_ROOT/skills/$SKILL_NAME"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
TARGET_PARENT="$CODEX_HOME_DIR/skills"
TARGET_LINK="$TARGET_PARENT/$SKILL_NAME"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "Error: skill directory not found: $SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$TARGET_PARENT"

if [ -L "$TARGET_LINK" ]; then
  CURRENT_TARGET=$(readlink "$TARGET_LINK")
  if [ "$CURRENT_TARGET" = "$SOURCE_DIR" ]; then
    echo "Skill already installed: $TARGET_LINK -> $SOURCE_DIR"
    exit 0
  fi
  rm "$TARGET_LINK"
elif [ -e "$TARGET_LINK" ]; then
  echo "Error: target already exists and is not a symlink: $TARGET_LINK" >&2
  echo "Move it away first, then rerun this script." >&2
  exit 1
fi

ln -s "$SOURCE_DIR" "$TARGET_LINK"
echo "Installed $SKILL_NAME: $TARGET_LINK -> $SOURCE_DIR"
