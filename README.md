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

1. Clone/download this repository and run the bootstrap.

```sh
cd ~/Developer/personal/python/macos-terminal-bootstrap
./install.sh
```

`install.sh` installs Homebrew when needed, installs `asdf`, installs Python and `uv` through ASDF, and then runs the installer through `uv run`.

2. Open Ghostty or reload the config with `Cmd+R`.

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

This repository does not configure Git identity, GitHub CLI authentication, commit signing, or SSH keys. That should live in a separate personal Git/SSH bootstrap so terminal appearance and shell setup stay separate from credentials and identity.

Manual checklist after installing this repository:

- Create or restore the personal SSH key.
- Add the public key to the personal GitHub account.
- Run `gh auth login` with the personal account.
- Configure `git config --global user.name` and `git config --global user.email`.
- Fill `~/.config/ramon-terminal/zsh/secrets.zsh` with the required tokens.

## Development

```sh
uv run python -m unittest discover -s tests
uv run python -m compileall src tests
```
