#!/usr/bin/env bash
# Install project Claude skills to ~/.claude/skills/
set -euo pipefail

SKILLS_SRC="$(cd "$(dirname "$0")/.claude/skills" && pwd)"
SKILLS_DST="$HOME/.claude/skills"

mkdir -p "$SKILLS_DST"

for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name="$(basename "$skill_dir")"
    cp -r "$skill_dir" "$SKILLS_DST/$skill_name"
    echo "installed: $skill_name → $SKILLS_DST/$skill_name"
done

echo "done — $(ls "$SKILLS_SRC" | wc -l) skill(s) installed"
