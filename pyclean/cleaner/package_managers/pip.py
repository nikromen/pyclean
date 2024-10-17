import os
import site
from subprocess import PIPE, run
from typing import Optional

import pkg_resources
from tqdm import tqdm

from pyclean.cleaner.package_managers.base import PackageInfo, PackageManager
from pyclean.constants import PkgType


class Pip(PackageManager):
    def __init__(self, system_clean: bool) -> None:
        super().__init__(system_clean)
        self.pkg_type = PkgType.pip

    # pip sometimes don't know what installer installed system package eventhough it knows about it
    # and lists it. On RPMs systems this could be local rpm installation or Copr...
    @staticmethod
    def _package_has_different_installer(name: str, version: str) -> bool:
        if run(["rpm", "--version"], stdout=PIPE).returncode != 0:
            return False

        process = run(
            ["rpm", "-q", "--queryformat", r"%{VERSION}\n", name],
            stdout=PIPE,
            check=True,
            text=True,
        )

        if process.returncode != 0:
            return False

        return process.stdout.strip() == version

    def _process_pip_package(
        self,
        dist: pkg_resources.Distribution,
    ) -> Optional[PackageInfo]:
        if dist.egg_info is None or dist.location is None:
            raise ValueError("egg_info or location does not exist.")

        path = os.path.join(dist.location, dist.egg_info, "RECORD")
        with open(path) as record_file:
            package_files = [line.split(",")[0] for line in record_file]

            installer = None
            if dist.has_metadata("INSTALLER"):
                with open(f"{dist.egg_info}/INSTALLER") as file:
                    installer = file.read().strip()

            if installer != PkgType.pip and installer in PkgType:
                return None

            if installer is None and self._package_has_different_installer(
                dist.project_name,
                dist.version,
            ):
                return None

            return PackageInfo(
                name=dist.project_name,
                package_name=dist.project_name,
                version=dist.version,
                location=dist.location,
                files=package_files,
                pkg_type=PkgType.pip if installer else None,
            )

    def get_python_packages(self) -> list[PackageInfo]:
        result = []
        for dist in tqdm(pkg_resources.working_set, desc="Processing pip packages"):
            tqdm.write(f"Processing pip package: {dist.project_name}")

            if not self.system_clean and dist.location != site.USER_SITE:
                continue

            if not dist.has_metadata("RECORD"):
                continue

            package = self._process_pip_package(dist)
            if package:
                result.append(package)

        return result

    def remove_python_packages(self, packages: set[str], auto_remove: bool) -> None:
        for package in tqdm(packages, desc="Removing pip packages"):
            tqdm.write(f"Removing pip package: {package}")
            cmd = ["pip", "uninstall"]
            if self.system_clean and os.geteuid() != 0:
                raise PermissionError(
                    "You need to be root to remove system packages system-wide.",
                )

            run([*cmd, package], check=True)

    def exists(self) -> bool:
        possible_bins = ["pip", "pip3"]
        for binary in possible_bins:
            if run(["which", binary], stdout=PIPE).returncode == 0:
                return True

        return False
