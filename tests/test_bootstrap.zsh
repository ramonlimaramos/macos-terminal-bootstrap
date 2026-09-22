#!/bin/zsh
set -euo pipefail

repo="${0:A:h:h}"
fixture="$(mktemp -d)"
trap 'rm -rf "$fixture"' EXIT

sed '/^install_homebrew$/,$d' "$repo/install.sh" |
  sed "s|/opt/homebrew/bin/brew|$fixture/missing-arm-brew|g; s|/usr/local/bin/brew|$fixture/missing-intel-brew|g" > "$fixture/functions.zsh"
source "$fixture/functions.zsh"
command_exists() { return 1; }
if find_brew > "$fixture/output"; then
  print -u2 'FAIL: absent Homebrew reported success'
  exit 1
fi
[[ ! -s "$fixture/output" ]]
curl() { print 'echo bootstrap-installer-invoked'; }
[[ "$(install_homebrew)" == *bootstrap-installer-invoked* ]]

mkdir "$fixture/bin"
printf '#!/bin/sh\nexit 0\n' > "$fixture/bin/brew"
chmod +x "$fixture/bin/brew"
export PATH="$fixture/bin:$PATH"
command_exists() { command -v "$1" >/dev/null 2>&1; }
[[ "$(find_brew)" == "$fixture/bin/brew" ]]
[[ -z "$(install_homebrew)" ]]
print 'PASS: Homebrew missing and PATH discovery'
