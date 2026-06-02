#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h}"

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

find_brew() {
  if [[ -x /opt/homebrew/bin/brew ]]; then
    echo /opt/homebrew/bin/brew
  elif [[ -x /usr/local/bin/brew ]]; then
    echo /usr/local/bin/brew
  elif command_exists brew; then
    command -v brew
  fi
}

install_homebrew() {
  if find_brew >/dev/null; then
    return
  fi

  echo "Homebrew not found. Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
}

install_homebrew
BREW="$(find_brew)"

if ! "$BREW" list --formula asdf >/dev/null 2>&1; then
  echo "Installing asdf through Homebrew..."
  "$BREW" install asdf
fi

cd "$ROOT_DIR"

if [[ -s "$HOME/.asdf/asdf.sh" ]]; then
  . "$HOME/.asdf/asdf.sh"
elif [[ -s "$("$BREW" --prefix asdf)/libexec/asdf.sh" ]]; then
  . "$("$BREW" --prefix asdf)/libexec/asdf.sh"
fi

PYTHON_VERSION="$(awk '$1 == "python" { print $2; exit }' "$ROOT_DIR/src/macos_terminal_bootstrap/assets/config/tool-versions")"
UV_VERSION="$(awk '$1 == "uv" { print $2; exit }' "$ROOT_DIR/src/macos_terminal_bootstrap/assets/config/tool-versions")"

if [[ -z "$PYTHON_VERSION" ]]; then
  echo "Could not find a Python version in assets/config/tool-versions." >&2
  exit 1
fi
if [[ -z "$UV_VERSION" ]]; then
  echo "Could not find a uv version in assets/config/tool-versions." >&2
  exit 1
fi

for plugin in python uv; do
  if ! asdf plugin list | grep -qx "$plugin"; then
    asdf plugin add "$plugin"
  fi
done

if ! asdf list python 2>/dev/null | sed 's/^[ *]*//' | grep -qx "$PYTHON_VERSION"; then
  echo "Installing Python $PYTHON_VERSION through asdf..."
  asdf install python "$PYTHON_VERSION"
fi
if ! asdf list uv 2>/dev/null | sed 's/^[ *]*//' | grep -qx "$UV_VERSION"; then
  echo "Installing uv $UV_VERSION through asdf..."
  asdf install uv "$UV_VERSION"
fi

export PATH="$(asdf where uv "$UV_VERSION")/bin:$(asdf where python "$PYTHON_VERSION")/bin:$PATH"
exec uv run ramon-terminal-bootstrap install "$@"
