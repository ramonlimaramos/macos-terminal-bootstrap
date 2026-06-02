from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from importlib.resources import files
from pathlib import Path


BREW_FORMULAS = ("git", "starship", "asdf", "fzf", "fd", "bat", "eza", "zoxide", "pipx", "glow")
BREW_CASKS = ("ghostty", "font-hack-nerd-font")
ASDF_PLUGINS = ("rust", "uv", "nodejs", "python", "terraform")

GIT_REPOS = (
    (
        "oh-my-zsh",
        "https://github.com/ohmyzsh/ohmyzsh.git",
        ".oh-my-zsh",
    ),
    (
        "zsh-autosuggestions",
        "https://github.com/zsh-users/zsh-autosuggestions.git",
        ".oh-my-zsh/custom/plugins/zsh-autosuggestions",
    ),
    (
        "zsh-syntax-highlighting",
        "https://github.com/zsh-users/zsh-syntax-highlighting.git",
        ".oh-my-zsh/custom/plugins/zsh-syntax-highlighting",
    ),
    (
        "nvm",
        "https://github.com/nvm-sh/nvm.git",
        ".nvm",
    ),
)

CONFIG_FILES = (
    ("ghostty/config", ".config/ghostty/config"),
    ("ghostty/typed_scramble.glsl", ".config/ghostty/typed_scramble.glsl"),
    (
        "ghostty/ghostty-cursor-shaders/cursor_warp.glsl",
        ".config/ghostty/ghostty-cursor-shaders/cursor_warp.glsl",
    ),
    (
        "ghostty/ghostty-shaders/mnoise.glsl",
        ".config/ghostty/ghostty-shaders/mnoise.glsl",
    ),
    ("config/starship.toml", ".config/starship.toml"),
    ("config/glow-dracula-preview.json", ".config/glow/dracula-preview.json"),
    ("zsh/zshrc", ".zshrc"),
    ("zsh/zprofile", ".zprofile"),
    ("config/tool-versions", ".tool-versions"),
)


@dataclass(frozen=True)
class InstallOptions:
    home: Path = field(default_factory=Path.home)
    dry_run: bool = False
    install_dependencies: bool = True
    install_configs: bool = True


class Installer:
    def __init__(self, options: InstallOptions) -> None:
        self.options = options
        self.home = options.home.expanduser().resolve()
        self.asset_root = files("macos_terminal_bootstrap").joinpath("assets")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.backup_root = self.home / ".terminal-bootstrap-backups" / timestamp

    def plan(self, include_dependencies: bool = True) -> None:
        print(f"Target home: {self.home}")
        if include_dependencies:
            print("\nDependencies:")
            for formula in BREW_FORMULAS:
                print(f"  brew formula: {formula}")
            for cask in BREW_CASKS:
                print(f"  brew cask: {cask}")
            for name, _url, rel_target in GIT_REPOS:
                print(f"  git repo: {name} -> ~/{rel_target}")
            for plugin in ASDF_PLUGINS:
                print(f"  asdf plugin: {plugin}")

        print("\nManaged files:")
        for _asset_rel, target_rel in CONFIG_FILES:
            print(f"  ~/{target_rel}")
        print("  ~/.config/ramon-terminal/zsh/local.zsh (created only if missing)")
        print("\nBackups:")
        print(f"  {self.backup_root}")

    def install(self) -> None:
        if self.options.install_dependencies:
            self.install_dependencies()
        if self.options.install_configs:
            self.install_configs()
        if self.options.install_dependencies:
            self._install_asdf_tool_versions()
        self.doctor(quiet=False)

    def install_dependencies(self) -> None:
        brew = self._find_brew()
        if brew is None:
            print("brew not found; skipping Homebrew packages. Install Homebrew and rerun.")
        else:
            for formula in BREW_FORMULAS:
                if not self._brew_has(brew, "--formula", formula):
                    self._run([brew, "install", formula])
                else:
                    print(f"ok: brew formula {formula}")
            for cask in BREW_CASKS:
                if not self._brew_has(brew, "--cask", cask):
                    self._run([brew, "install", "--cask", cask])
                else:
                    print(f"ok: brew cask {cask}")

        git = shutil.which("git")
        if git is None:
            print("git not found; skipping git-based shell dependencies.")
            return

        for name, url, rel_target in GIT_REPOS:
            self._ensure_git_repo(git, name, url, self.home / rel_target)
        self._ensure_asdf_plugins()

    def install_configs(self) -> None:
        for asset_rel, target_rel in CONFIG_FILES:
            self._write_asset(asset_rel, self.home / target_rel)
        self._write_asset(
            "zsh/local.zsh",
            self.home / ".config/ramon-terminal/zsh/local.zsh",
            overwrite=False,
        )

    def doctor(self, quiet: bool = False) -> bool:
        checks: list[tuple[str, bool, str]] = []
        checks.append(("brew", self._find_brew() is not None, "Homebrew is available"))
        for command in ("git", "zsh", "starship"):
            checks.append((command, shutil.which(command) is not None, f"{command} is on PATH"))

        for _asset_rel, target_rel in CONFIG_FILES:
            target = self.home / target_rel
            checks.append((target_rel, target.exists(), f"expected at {target}"))

        local_zsh = self.home / ".config/ramon-terminal/zsh/local.zsh"
        checks.append(("local.zsh", local_zsh.exists(), f"expected at {local_zsh}"))

        ok = True
        for name, passed, message in checks:
            ok = ok and passed
            if quiet and passed:
                continue
            status = "ok" if passed else "missing"
            print(f"{status}: {name} - {message}")

        ghostty = self._find_ghostty()
        if ghostty is not None and self.home == Path.home().resolve():
            result = self._run([ghostty, "+validate-config"], check=False, capture=True)
            passed = result.returncode == 0
            ok = ok and passed
            if not quiet or not passed:
                status = "ok" if passed else "failed"
                print(f"{status}: ghostty +validate-config")
                if result.stderr:
                    print(result.stderr.strip())
        elif not quiet:
            print("skipped: ghostty +validate-config")

        return ok

    def _write_asset(self, asset_rel: str, target: Path, overwrite: bool = True) -> None:
        data = self.asset_root.joinpath(asset_rel).read_bytes()
        if target.exists() and target.read_bytes() == data:
            print(f"ok: {target}")
            return
        if target.exists() and not overwrite:
            print(f"kept: {target}")
            return

        if target.exists():
            backup = self.backup_root / target.relative_to(self.home)
            self._copy_existing(target, backup)
        self._write_bytes(target, data)

    def _write_bytes(self, target: Path, data: bytes) -> None:
        if self.options.dry_run:
            print(f"would write: {target}")
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"wrote: {target}")

    def _copy_existing(self, source: Path, backup: Path) -> None:
        if self.options.dry_run:
            print(f"would backup: {source} -> {backup}")
            return
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, backup)
        print(f"backup: {source} -> {backup}")

    def _ensure_git_repo(self, git: str, name: str, url: str, target: Path) -> None:
        if (target / ".git").exists():
            print(f"ok: {name} at {target}")
            return
        if target.exists():
            print(f"kept: {target} exists but is not a git checkout; clone skipped.")
            return
        self._run([git, "clone", "--depth", "1", url, str(target)])

    def _ensure_asdf_plugins(self) -> None:
        asdf = self._find_asdf()
        if asdf is None:
            print("asdf not found; skipping ASDF plugins.")
            return

        result = self._run([asdf, "plugin", "list"], check=False, capture=True)
        installed = set(result.stdout.splitlines()) if result.returncode == 0 else set()
        for plugin in ASDF_PLUGINS:
            if plugin in installed:
                print(f"ok: asdf plugin {plugin}")
            else:
                self._run([asdf, "plugin", "add", plugin], check=False)

    def _install_asdf_tool_versions(self) -> None:
        asdf = self._find_asdf()
        if asdf is None:
            print("asdf not found; skipping ASDF tool installs.")
            return

        tool_versions = self.home / ".tool-versions"
        if not tool_versions.exists():
            print(f"{tool_versions} not found; skipping ASDF tool installs.")
            return

        self._run([asdf, "install"], check=False)

    def _brew_has(self, brew: str, kind: str, package: str) -> bool:
        result = self._run([brew, "list", kind, package], check=False, capture=True)
        return result.returncode == 0

    def _find_brew(self) -> str | None:
        candidates = ("/opt/homebrew/bin/brew", "/usr/local/bin/brew", shutil.which("brew"))
        return next((candidate for candidate in candidates if candidate and Path(candidate).exists()), None)

    def _find_asdf(self) -> str | None:
        candidates = (
            str(self.home / ".asdf/bin/asdf"),
            "/opt/homebrew/bin/asdf",
            "/usr/local/bin/asdf",
            shutil.which("asdf"),
        )
        return next((candidate for candidate in candidates if candidate and Path(candidate).exists()), None)

    def _find_ghostty(self) -> str | None:
        candidates = (
            "/Applications/Ghostty.app/Contents/MacOS/ghostty",
            shutil.which("ghostty"),
        )
        return next((candidate for candidate in candidates if candidate and Path(candidate).exists()), None)

    def _run(
        self,
        command: list[str],
        *,
        check: bool = True,
        capture: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        printable = " ".join(command)
        if self.options.dry_run:
            print(f"would run: {printable}")
            return subprocess.CompletedProcess(command, 0, "", "")

        print(f"run: {printable}")
        return subprocess.run(
            command,
            check=check,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            env=os.environ.copy(),
        )
