# macos-terminal-bootstrap

<p align="center">
  <img src="docs/terminal-preview.png" alt="Terminal preview after bootstrap" width="100%">
</p>

Bootstrap the terminal setup currently used on this Mac:

- Ghostty with the Dracula theme, cursor warp, typed scramble, and subtle noise.
- Zsh with Oh My Zsh, `git`, `zsh-autosuggestions`, and `zsh-syntax-highlighting`.
- Starship with a lean Dracula palette.
- Modern CLI tooling: `fzf`, `fd`, `bat`, `eza`, `zoxide`, `glow`.
- Optional local files for aliases, tokens, and work-specific settings.

This project does not version secrets. Tokens, private keys, and sensitive environment variables should live in:

```sh
~/.config/ramon-terminal/zsh/secrets.zsh
```

## Installation On A New Mac

1. If migrating, transfer your private `secrets.zsh` to Downloads on the new
Mac (for example, using AirDrop). On the old Mac, the intended location is
`~/.config/ramon-terminal/zsh/secrets.zsh`. If it does not exist, collect only
the required secret exports from your existing shell configuration. Resolve
references to old project `.env` files before transferring; do not copy your
entire old `.zshrc` or commit credentials to this repository.

2. In Terminal on the **new Mac**, install the transferred file:

```sh
mkdir -p ~/.config/ramon-terminal/zsh
install -m 600 ~/Downloads/secrets.zsh ~/.config/ramon-terminal/zsh/secrets.zsh
```

Skip this step if you do not need private environment variables. If you already
have a secrets file on the new Mac, merge the required exports instead of
overwriting it. Non-secret customizations belong in `local.zsh` alongside it.

3. Paste this block into Terminal from any directory; no GitHub login or clone
is required:

```zsh
(
  set -e
  setup_dir="$(mktemp -d)"
  curl -fsSL \
    https://github.com/ramonlimaramos/macos-terminal-bootstrap/archive/refs/heads/main.tar.gz \
    -o "$setup_dir/bootstrap.tar.gz"
  tar -xzf "$setup_dir/bootstrap.tar.gz" -C "$setup_dir"
  /bin/zsh "$setup_dir/macos-terminal-bootstrap-main/install.sh"
)
```

Alternatively, from an existing checkout:

```sh
cd ~/Developer/personal/python/macos-terminal-bootstrap
./install.sh
```

`install.sh` installs Homebrew when needed, installs `asdf`, installs Python and `uv` through ASDF, and then runs the installer through `uv run`.

The installer may request your macOS password and installation confirmations.
Paths use `~` and `$HOME`: a new account named `ramon.ramos` works even if the
old account was named `ramonramos`. Review absolute paths in your own local files.

4. Open a new terminal window to load the configuration and secrets. Open
Ghostty or reload its config with `Cmd+R`.

To review before applying:

```sh
uv run ramon-terminal-bootstrap plan
uv run ramon-terminal-bootstrap install --dry-run
```

## Commands

```sh
uv run ramon-terminal-bootstrap plan
uv run ramon-terminal-bootstrap install
uv run ramon-terminal-bootstrap install --dry-run
uv run ramon-terminal-bootstrap doctor
```

After installing in editable mode:

```sh
uv pip install -e .
ramon-terminal-bootstrap doctor
```

## What The Installer Does

- Installs Homebrew when called through `./install.sh`.
- Installs `asdf` through Homebrew before running the bootstrap.
- Installs Python and `uv` through ASDF before executing the project.
- Installs Homebrew packages when `brew` is available: `git`, `starship`, `asdf`, `fzf`, `fd`, `bat`, `eza`, `zoxide`, `glow`, `pipx`, `ghostty`, and `font-hack-nerd-font`.
- Clones Oh My Zsh and custom plugins when they do not exist.
- Adds ASDF plugins for `rust`, `uv`, `nodejs`, `python`, and `terraform`, then runs `asdf install`.
- Copies configs to:
  - `~/.config/ghostty/config`
  - `~/.config/ghostty/typed_scramble.glsl`
  - `~/.config/ghostty/ghostty-cursor-shaders/cursor_warp.glsl`
  - `~/.config/ghostty/ghostty-shaders/mnoise.glsl`
  - `~/.config/starship.toml`
  - `~/.config/glow/dracula-preview.json`
  - `~/.zshrc`
  - `~/.zprofile`
  - `~/.tool-versions`
- Backs up any existing file before overwriting it:

```sh
~/.terminal-bootstrap-backups/<timestamp>/
```

## Secrets And Local Files

The installed `.zshrc` loads these files when they exist:

```sh
~/.config/ramon-terminal/zsh/local.zsh
~/.config/ramon-terminal/zsh/secrets.zsh
```

Use `local.zsh` for aliases and functions that do not contain secrets. Use `secrets.zsh` for tokens and sensitive environment variables. The installer only creates a safe `local.zsh` when it does not already exist.

## Out Of Scope

This repository does not configure Git identity, GitHub CLI authentication,
commit signing, SSH keys, or corporate access. Continue with
[ramon-git-bootstrap](https://github.com/ramonlimaramos/ramon-git-bootstrap)
for Git/GitHub/SSH setup. Installing this project does not replicate all
applications or credentials from the old Mac.

Manual checklist after installing this repository:

- Create or restore the personal SSH key.
- Add the public key to the personal GitHub account.
- Run `gh auth login` with the personal account.
- Configure personal/professional identities through the Git bootstrap.
- Fill `~/.config/ramon-terminal/zsh/secrets.zsh` with the required tokens.

## Development

```sh
zsh -n install.sh
shellcheck --shell=bash --exclude=SC1091 install.sh
zsh tests/test_bootstrap.zsh
uv run python -m unittest discover -s tests
uv run python -m compileall src tests
```
