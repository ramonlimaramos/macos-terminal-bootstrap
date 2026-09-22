from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from macos_terminal_bootstrap.installer import CONFIG_FILES, InstallOptions, Installer


class InstallerTest(unittest.TestCase):
    def test_install_configs_writes_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            home = Path(tempdir)
            installer = Installer(
                InstallOptions(home=home, install_dependencies=False, install_configs=True)
            )

            installer.install_configs()

            for _asset_rel, target_rel in CONFIG_FILES:
                self.assertTrue((home / target_rel).exists(), target_rel)
            self.assertTrue((home / ".config/ramon-terminal/zsh/local.zsh").exists())

    def test_existing_files_are_backed_up_before_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            home = Path(tempdir)
            target = home / ".zshrc"
            target.write_text("old config\n")

            installer = Installer(InstallOptions(home=home, install_dependencies=False))
            installer.install_configs()

            backups = list((home / ".terminal-bootstrap-backups").glob("*/.zshrc"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), "old config\n")
            self.assertIn("macos-terminal-bootstrap", target.read_text())

    def test_local_zsh_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            home = Path(tempdir)
            local_zsh = home / ".config/ramon-terminal/zsh/local.zsh"
            local_zsh.parent.mkdir(parents=True)
            local_zsh.write_text("alias custom=true\n")

            installer = Installer(InstallOptions(home=home, install_dependencies=False))
            installer.install_configs()

            self.assertEqual(local_zsh.read_text(), "alias custom=true\n")

    def test_assets_do_not_contain_obvious_secret_tokens(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        suspicious = (
            "gl" + "pat-",
            "gh" + "p_",
            "github" + "_pat_",
            "xo" + "xb-",
            "xa" + "pp-",
            "np" + "m_",
            "BEGIN " + "PRIVATE KEY",
        )
        roots_to_scan = (
            project_root / "README.md",
            project_root / "bootstrap.py",
            project_root / "pyproject.toml",
            project_root / "src",
        )
        offenders: list[Path] = []

        paths: list[Path] = []
        for root in roots_to_scan:
            if root.is_file():
                paths.append(root)
            else:
                paths.extend(path for path in root.rglob("*") if path.is_file())

        for path in paths:
            text = path.read_text(errors="ignore")
            if any(token in text for token in suspicious):
                offenders.append(path.relative_to(project_root))

        self.assertEqual(offenders, [])

    def test_update_preserves_local_files_and_refreshes_managed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            home = Path(tempdir) / "ramon.ramos"
            installer = Installer(InstallOptions(home=home, install_dependencies=False))
            installer.install_configs()
            local_files = (
                ".config/ramon-terminal/zsh/local.zsh",
                ".config/ramon-terminal/zsh/secrets.zsh",
                ".config/ghostty/local.conf",
            )
            for relative in local_files:
                (home / relative).write_text("private local configuration\n")
            ghostty = home / ".config/ghostty/config"
            ghostty.write_text("background-opacity = 0.85\n")
            updater = home / ".local/bin/ramon-terminal-update"
            updater.write_text("old updater\n")
            updater.chmod(0o644)

            update = Installer(InstallOptions(home=home, install_dependencies=False))
            update.install_configs()

            for relative in local_files:
                self.assertEqual((home / relative).read_text(), "private local configuration\n")
            self.assertIn("background-opacity = 0.93", ghostty.read_text())
            self.assertNotIn("custom-shader = typed_scramble.glsl", ghostty.read_text())
            self.assertIn("config-file = ?local.conf", ghostty.read_text())
            self.assertIn("cursor_warp.glsl", ghostty.read_text())
            self.assertIn("mnoise.glsl", ghostty.read_text())
            self.assertTrue(updater.stat().st_mode & 0o111)
            self.assertIn("archive/refs/heads/main.tar.gz", updater.read_text())
            self.assertEqual(
                (update.backup_root / ".config/ghostty/config").read_text(),
                "background-opacity = 0.85\n",
            )
            self.assertEqual(
                (update.backup_root / ".local/bin/ramon-terminal-update").read_text(),
                "old updater\n",
            )
            repeated = Installer(InstallOptions(home=home, install_dependencies=False))
            repeated.install_configs()
            self.assertFalse(repeated.backup_root.exists())

    def test_config_dry_run_does_not_create_home(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            home = Path(tempdir) / "ramon.ramos"
            Installer(InstallOptions(home=home, dry_run=True)).install_configs()
            self.assertFalse(home.exists())

    def test_asdf_installs_versions_from_target_home(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            home = Path(tempdir)
            (home / ".tool-versions").write_text("python 3.13.1\n")
            installer = Installer(InstallOptions(home=home))
            with (
                patch.object(installer, "_find_asdf", return_value="/fake/asdf"),
                patch("macos_terminal_bootstrap.installer.subprocess.run") as run,
            ):
                installer._install_asdf_tool_versions()
            self.assertEqual(run.call_args.args[0], ["/fake/asdf", "install"])
            self.assertEqual(run.call_args.kwargs["cwd"], home.resolve())
            self.assertTrue(run.call_args.kwargs["check"])

    def test_asdf_install_failure_is_not_reported_as_success(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            home = Path(tempdir)
            (home / ".tool-versions").write_text("python 3.13.1\n")
            installer = Installer(InstallOptions(home=home))
            with (
                patch.object(installer, "_find_asdf", return_value="/fake/asdf"),
                patch(
                    "macos_terminal_bootstrap.installer.subprocess.run",
                    side_effect=subprocess.CalledProcessError(1, ["/fake/asdf", "install"]),
                ),
                self.assertRaises(subprocess.CalledProcessError),
            ):
                installer._install_asdf_tool_versions()


if __name__ == "__main__":
    unittest.main()
