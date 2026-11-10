#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./install.sh [options] <target-project>

Install/update portable Faultline skills and optional native agent adapters.

Options:
  --dry-run                Preview intended changes only.
  --force                  Replace existing Faultline-owned skills/agent files
                           and refresh only the marked Faultline AGENTS.md block.
  --no-antigravity-agents  Skip .agents/agents/ adapters.
  --no-opencode-agents     Skip .opencode/agents/ adapters.
  -h, --help               Show this help.
USAGE
}

DRY_RUN=0
FORCE=0
INSTALL_AG=1
INSTALL_OC=1
TARGET=""
while (($#)); do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --force) FORCE=1; shift ;;
    --no-antigravity-agents) INSTALL_AG=0; shift ;;
    --no-opencode-agents) INSTALL_OC=0; shift ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    *)
      if [[ -n "$TARGET" ]]; then
        echo "Only one target project is supported." >&2
        exit 2
      fi
      TARGET="$1"
      shift
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then usage >&2; exit 2; fi
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$(mkdir -p "$TARGET" && cd "$TARGET" && pwd)"

mapfile -t SKILLS < <(find "$SCRIPT_DIR/.agents/skills" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
AGENT_FILES=()
OC_AGENT_FILES=()
if [[ "$INSTALL_AG" -eq 1 ]]; then
  mapfile -t AGENT_FILES < <(find "$SCRIPT_DIR/.agents/agents" -maxdepth 1 -type f -name 'faultline-*.md' -printf '%f\n' | sort)
fi
if [[ "$INSTALL_OC" -eq 1 ]]; then
  mapfile -t OC_AGENT_FILES < <(find "$SCRIPT_DIR/.opencode/agents" -maxdepth 1 -type f -name 'faultline-*.md' -printf '%f\n' | sort)
fi

check_collision() {
  local destination="$1"
  if [[ -e "$destination" && "$FORCE" -ne 1 ]]; then
    echo "ERROR: $destination already exists. Use --force to replace Faultline-owned content." >&2
    exit 1
  fi
}
for skill in "${SKILLS[@]}"; do check_collision "$TARGET/.agents/skills/$skill"; done
for file in "${AGENT_FILES[@]}"; do check_collision "$TARGET/.agents/agents/$file"; done
for file in "${OC_AGENT_FILES[@]}"; do check_collision "$TARGET/.opencode/agents/$file"; done

AGENTS_MD="$TARGET/AGENTS.md"
SNIPPET="$SCRIPT_DIR/integrations/AGENTS.md.snippet"
START='<!-- faultline:start -->'
END='<!-- faultline:end -->'
if [[ -f "$AGENTS_MD" ]] && grep -Fqx "$START" "$AGENTS_MD"; then
  if ! grep -Fqx "$END" "$AGENTS_MD"; then
    echo "ERROR: $AGENTS_MD has an unmatched Faultline start marker. Repair it manually; refusing to truncate existing rules." >&2
    exit 1
  fi
  if [[ "$FORCE" -ne 1 ]]; then
    echo "ERROR: Faultline block already exists in $AGENTS_MD. Use --force to refresh it." >&2
    exit 1
  fi
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Would install skills: ${SKILLS[*]}"
  echo "Would install Antigravity agents: ${AGENT_FILES[*]:-(none)}"
  echo "Would install OpenCode agents: ${OC_AGENT_FILES[*]:-(none)}"
  echo "Would append/refresh only the marked Faultline block in: $AGENTS_MD"
  exit 0
fi

mkdir -p "$TARGET/.agents/skills"
for skill in "${SKILLS[@]}"; do
  rm -rf -- "$TARGET/.agents/skills/$skill"
  cp -a -- "$SCRIPT_DIR/.agents/skills/$skill" "$TARGET/.agents/skills/$skill"
  echo "Installed skill: $skill"
done

if [[ "$INSTALL_AG" -eq 1 ]]; then
  mkdir -p "$TARGET/.agents/agents"
  for file in "${AGENT_FILES[@]}"; do
    rm -f -- "$TARGET/.agents/agents/$file"
    cp -- "$SCRIPT_DIR/.agents/agents/$file" "$TARGET/.agents/agents/$file"
  done
fi
if [[ "$INSTALL_OC" -eq 1 ]]; then
  mkdir -p "$TARGET/.opencode/agents"
  for file in "${OC_AGENT_FILES[@]}"; do
    rm -f -- "$TARGET/.opencode/agents/$file"
    cp -- "$SCRIPT_DIR/.opencode/agents/$file" "$TARGET/.opencode/agents/$file"
  done
fi

if [[ -f "$AGENTS_MD" ]] && grep -Fqx "$START" "$AGENTS_MD"; then
  tmp="$(mktemp)"
  awk -v start="$START" -v end="$END" '
    $0 == start { skip=1; next }
    $0 == end { skip=0; next }
    !skip { print }
  ' "$AGENTS_MD" > "$tmp"
  cat "$tmp" > "$AGENTS_MD"
  rm -f "$tmp"
fi
{
  [[ ! -s "$AGENTS_MD" ]] || printf '\n'
  cat "$SNIPPET"
  printf '\n'
} >> "$AGENTS_MD"

echo "Updated $AGENTS_MD"
echo "Faultline $(cat "$SCRIPT_DIR/VERSION" | tr -d '\n') installed into $TARGET"
echo "Reload the agent. Use faultline-preflight or faultline-break-sweep; review changes before committing."
