from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
