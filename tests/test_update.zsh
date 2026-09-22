#!/bin/zsh
set -euo pipefail

repo="${0:A:h:h}"
fixture="$(mktemp -d)"
trap 'rm -rf "$fixture"' EXIT
export HOME="$fixture/ramon.ramos"
export TMPDIR="$fixture/downloads"
mkdir -p "$HOME" "$TMPDIR" "$fixture/bin" "$fixture/source/macos-terminal-bootstrap-main"
export UPDATE_TEST_MARKER="$fixture/installed"
export UPDATE_TEST_ARCHIVE="$fixture/source.tar.gz"

cat > "$fixture/source/macos-terminal-bootstrap-main/install.sh" <<'INSTALL'
#!/bin/zsh
print applied > "$UPDATE_TEST_MARKER"
exit "${UPDATE_TEST_INSTALL_EXIT:-0}"
INSTALL
tar -czf "$UPDATE_TEST_ARCHIVE" -C "$fixture/source" macos-terminal-bootstrap-main
cat > "$fixture/bin/curl" <<'CURL'
#!/bin/zsh
if [[ "${UPDATE_TEST_DOWNLOAD_FAIL:-0}" == 1 ]]; then
  exit 22
fi
[[ "$2" == https://github.com/ramonlimaramos/macos-terminal-bootstrap/archive/refs/heads/main.tar.gz ]] || exit 2
cp "$UPDATE_TEST_ARCHIVE" "$4"
CURL
chmod +x "$fixture/bin/curl"
export PATH="$fixture/bin:$PATH"
updater="$repo/src/macos_terminal_bootstrap/assets/zsh/ramon-terminal-update"

zsh "$updater" > "$fixture/success.log"
[[ "$(cat "$UPDATE_TEST_MARKER")" == applied ]]
[[ -z "$(ls -A "$TMPDIR")" ]]
rm "$UPDATE_TEST_MARKER"

if UPDATE_TEST_DOWNLOAD_FAIL=1 zsh "$updater" > "$fixture/download-failure.log" 2>&1; then
  print -u2 'FAIL: download failure reported success'
  exit 1
fi
[[ ! -e "$UPDATE_TEST_MARKER" ]]
[[ -z "$(ls -A "$TMPDIR")" ]]

if UPDATE_TEST_INSTALL_EXIT=7 zsh "$updater" > "$fixture/install-failure.log" 2>&1; then
  print -u2 'FAIL: installer failure reported success'
  exit 1
fi
[[ -z "$(ls -A "$TMPDIR")" ]]
if grep -q 'Updated from main' "$fixture/install-failure.log"; then
  print -u2 'FAIL: success message after installer failure'
  exit 1
fi
print 'PASS: updater applies main, propagates failures, and cleans up downloads'
