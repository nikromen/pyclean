from subprocess import run, PIPE

from pyrpm_clean.constants import PkgType


class Cleaner:
    def __init__(
        self, user_clean: bool
    ) -> None:
        # check package for the whole system if set to true
        # else check only packages in user-space (pip install --user)
        self.user_clean = user_clean

    def _get_packages(self, pkg_type: PkgType) -> set[str]:
        if pkg_type == PkgType.pypi:
            cmd = ["pip", "list"]
            if self.user_clean:
                cmd.append("--user")
            cmd += ["--format=columns"]
            process = run(cmd, stdout=PIPE, text=True, check=True)
            return {
                line.split()[0].strip()
                for line in process.stdout.strip().split("\n")[2:]
            }

        process = run(
            ["rpm", "-qa", "--queryformat", r'"%{NAME}\n"'],
            stdout=PIPE,
            check=True,
            text=True,
        )
        packages = process.stdout.split("\n")
        return {
            pkg.rstrip("python3-").rstrip("python-").strip()
            for pkg in packages
            if pkg.startswith("python-") or pkg.startswith("python3-")
        }

    def get_packages_to_clean(self) -> set[str]:
        return self._get_packages(PkgType.rpm) & self._get_packages(PkgType.pypi)

    def clean(self, clean_type: PkgType) -> None:
        pkgs_intersect = list(self.get_packages_to_clean())
        if clean_type == PkgType.rpm:
            run(["sudo", "-S", "dnf", "remove"] + pkgs_intersect + ["--noautoremove"])
            return

        # TODO: clean nasty pkgs under root if someone installed it under root
        run(["pip", "uninstall"] + pkgs_intersect)
