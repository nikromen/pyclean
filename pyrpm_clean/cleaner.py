import os
import site
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from subprocess import PIPE, run
from typing import Optional

import pkg_resources
from tqdm import tqdm

from pyrpm_clean.constants import CleanType, PkgType
from pyrpm_clean.helpers import dupe_table


@dataclass
class PackageInfo:
    name: str
    version: str
    location: Optional[str]
    files: list[str]
    pkg_type: Optional[PkgType] = None


class Cleaner:
    def __init__(self, system_clean: bool) -> None:
        self.system_clean = system_clean

    @staticmethod
    def _get_rpm_package_files(name: str) -> list[str]:
        files_process = run(["rpm", "-ql", name], stdout=PIPE, check=True, text=True)
        return files_process.stdout.strip().split("\n")

    @classmethod
    def _check_python_package_and_get_files(cls, name: str) -> Optional[list[str]]:
        if name.startswith(("python-", "python3-")):
            return cls._get_rpm_package_files(name)

        requires = (
            run(
                ["rpm", "-qR", name],
                stdout=PIPE,
                check=True,
                text=True,
            )
            .stdout.strip()
            .split("\n")
        )
        for req in requires:
            # looking for python binary as dependency
            if req.endswith(("python", "python3")):
                return cls._get_rpm_package_files(name)

        files = cls._get_rpm_package_files(name)
        for file in files:
            if not file.endswith((".py", ".pyc", ".pyo")):
                return None

        return files

    def _process_rpm_package(self, package: str) -> Optional[PackageInfo]:
        tqdm.write(f"Processing rpm package: {package}")

        name, version = package.split()
        files = self._check_python_package_and_get_files(name)
        if files is None:
            return None

        if name.startswith(("python-", "python3-")):
            parts = name.split("-")
            name = "-".join(parts[1:])

        location = None
        if files:
            # get basename of the first file, wild guess since that may not be true
            location = "/".join(files[0].split("/")[:-1])

        return PackageInfo(
            name=name,
            version=version,
            location=location,
            files=files,
            pkg_type=PkgType.rpm,
        )

    def _get_rpm_packages(self) -> list[PackageInfo]:
        process = run(
            ["rpm", "-qa", "--queryformat", r"%{NAME} %{VERSION}\n"],
            stdout=PIPE,
            check=True,
            text=True,
        )
        packages = process.stdout.strip().split("\n")
        result = []

        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(
                    self._process_rpm_package,
                    package,
                ): package
                for package in packages
            }

            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Processing rpm packages",
            ):
                package = future.result()
                if package:
                    result.append(package)

        return result

    @staticmethod
    def _package_has_rpm_installer(name: str, version: str) -> bool:
        process = run(
            ["rpm", "-q", "--queryformat", r"%{VERSION}\n", name],
            stdout=PIPE,
            check=True,
            text=True,
        )

        if process.returncode != 0:
            return False

        return process.stdout.strip() == version

    def _process_pypi_package(self, dist: pkg_resources.Distribution) -> Optional[PackageInfo]:
        if dist.egg_info is None or dist.location is None:
            raise ValueError("egg_info or location does not exist.")

        package_files = []
        path = os.path.join(dist.location, dist.egg_info, "RECORD")
        with open(path) as record_file:
            package_files = [line.split(",")[0] for line in record_file]

            installer = None
            if dist.has_metadata("INSTALLER"):
                with open(f"{dist.egg_info}/INSTALLER") as file:
                    installer = file.read().strip()

            if installer == PkgType.rpm.name:
                return None

            if installer is None and self._package_has_rpm_installer(
                dist.project_name,
                dist.version,
            ):
                return None

            return PackageInfo(
                name=dist.project_name,
                version=dist.version,
                location=dist.location,
                files=package_files,
                pkg_type=PkgType.pypi if installer else None,
            )

    def _get_pypi_packages(self) -> list[PackageInfo]:
        result = []
        for dist in tqdm(pkg_resources.working_set, desc="Processing pypi packages"):
            tqdm.write(f"Processing pypi package: {dist.project_name}")

            if not self.system_clean and dist.location != site.USER_SITE:
                continue

            if not dist.has_metadata("RECORD"):
                continue

            package = self._process_pypi_package(dist)
            if package:
                result.append(package)

        return result

    def get_packages_to_clean(self) -> dict[str, list[PackageInfo]]:
        rpm_pkgs = self._get_rpm_packages()
        pypi_pkgs = self._get_pypi_packages()
        dupes_per_package_name = {pkg.name for pkg in rpm_pkgs} & {pkg.name for pkg in pypi_pkgs}
        result: dict[str, list[PackageInfo]] = {name: [] for name in dupes_per_package_name}
        for pkg in rpm_pkgs + pypi_pkgs:
            if pkg.name in dupes_per_package_name:
                result[pkg.name].append(pkg)

        return result

    def rm_pypi_packages(self, packages: list[str]) -> None:
        for package in tqdm(packages, desc="Removing pypi packages"):
            tqdm.write(f"Removing pypi package: {package}")
            cmd = ["pip", "uninstall"]
            if self.system_clean and os.geteuid() != 0:
                raise PermissionError("You need to be root to remove system packages system-wide.")

            run([*cmd, package], check=True)

    @staticmethod
    def rm_rpm_packages(packages: list[str], autoremove: bool = False) -> None:
        cmd = ["sudo", "dnf", "remove"]
        if not autoremove:
            cmd.append("--noautoremove")

        run(cmd + packages)

    def _interactive_clean_step(self, package: str, autoremove: bool) -> None:
        print("\nDo you want to remove this package? [y/N]")
        if input().lower() != "y":
            return

        while True:
            print("\nChoose package type to remove:")
            print("1. pypi")
            print("2. rpm")
            print("3. Skip")
            choice = input()
            if choice == "1":
                self.rm_pypi_packages([package])
                break
            if choice == "2":
                self.rm_rpm_packages([package], autoremove)
                break
            if choice == "3":
                return
            print("Invalid choice.")

    def clean(self, clean_type: CleanType, autoremove: bool) -> None:
        dupes_d = self.get_packages_to_clean()
        dupes = list(dupes_d.keys())
        if not dupes:
            print("No packages to clean.")
            return

        if clean_type == CleanType.pypi:
            self.rm_pypi_packages(dupes)
            return

        if clean_type == CleanType.rpm:
            self.rm_rpm_packages(dupes, autoremove)
            return

        for package in dupes:
            print(dupe_table(package, dupes_d[package], verbose=False))
            print("")
            self._interactive_clean_step(package, autoremove)
