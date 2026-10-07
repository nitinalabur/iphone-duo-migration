#!/bin/bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_DIR="$(mktemp -d "${TMPDIR:-/tmp}/duo-layout-tests.XXXXXX")"
trap 'rm -rf "$TEST_DIR"' EXIT
xcrun --sdk macosx swiftc \
  -module-cache-path "$TEST_DIR/module-cache" \
  "$ROOT_DIR/skills/iphone-duo-migration/assets/DuoPaneLayout.swift" \
  "$ROOT_DIR/tests/layout/main.swift" \
  -o "$TEST_DIR/layout-tests"
"$TEST_DIR/layout-tests"
