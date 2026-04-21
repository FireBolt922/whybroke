#!/usr/bin/env bash
# Read-only preflight check for the whybroke skill.
# Prints a single line describing which mode the skill should run in.
# Never installs software, never triggers interactive auth.

set -u

if ! command -v whybroke >/dev/null 2>&1; then
  echo "mode=B reason=not_installed"
  exit 0
fi

if [ ! -f "${HOME}/.whybroke/credentials.json" ]; then
  echo "mode=B reason=not_authenticated"
  exit 0
fi

echo "mode=A"
