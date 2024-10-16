import os
import site
from subprocess import run, PIPE
from typing import Optional

from pyclean.cleaner.package_managers.base import PackageManager, PackageInfo
from tqdm import tqdm

from pyclean.constants import PkgType
from concurrent.futures import ThreadPoolExecutor, as_completed


class Rpm(PackageManager):
    def __init__(self, system_clean: bool) -> None:
        super().__init__(system_clean)
        self.pkg_type = PkgType.rpm

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

        package_name = name
        if name.startswith(("python-", "python3-")):
            parts = name.split("-")
            name = "-".join(parts[1:])

        location = None
        if files:
            # get basename of the first file, wild guess since that may not be true
            location = "/".join(files[0].split("/")[:-1])

        return PackageInfo(
            name=name,
            package_name=package_name,
            version=version,
            location=location,
            files=files,
            pkg_type=PkgType.rpm,
        )

    @staticmethod
    def _without_duplicates(packages: list[PackageInfo]) -> list[PackageInfo]:
        pkg_name_d = {pkg.name: [] for pkg in packages}
        for package in packages:
            pkg_name_d[package.name].append(package)

        result = []
        for pkg_name, pkgs in pkg_name_d.items():
            # no dupe, correct
            if len(pkgs) == 1:
                result.append(pkgs[0])
                continue

            # dupe, let's keep the binary package preferably without python3- prefix
            for pkg in pkgs:
                if pkg.package_name == pkg.name:
                    result.append(pkg)
                    break
            else:
                # TODO: what to ideally prefer?
                result.append(pkgs[0])

        return result

    def get_python_packages(self) -> list[PackageInfo]:
        process = run(
            ["rpm", "-qa", "--queryformat", r"%{NAME} %{VERSION}\n"],
            stdout=PIPE,
            check=True,
            text=True,
        )
        packages = process.stdout.strip().split("\n")
        parsed_packages = []

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
                    parsed_packages.append(package)

        # rpm may have python3- or python- prefix for the same package for python3 and 2 support
        # or it is just a library and python binary has the same name without prefix.
        # I trust rpm enough that it won't install same package twice to the system
        # so in case of dupes, let's just keep the binary package
        return self._without_duplicates(parsed_packages)

    def remove_python_packages(self, packages: set[str], auto_remove: bool) -> None:
        cmd = ["sudo", "dnf", "remove"]
        if not auto_remove:
            cmd.append("--noautoremove")

        run(cmd + list(packages))

    def exists(self) -> bool:
        return run(["which", "rpm"], stdout=PIPE).returncode == 0
