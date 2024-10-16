from pyclean.constants import PkgType
from pyclean.cleaner.package_managers.base import PackageManager, PackageInfo
from pyclean.cleaner.package_managers.rpm import Rpm
from pyclean.cleaner.package_managers.pip import Pip
from pyclean.cleaner.package_managers.pipx import Pipx

from tqdm import tqdm

from pyclean.helpers import dupe_table


class Cleaner:
    def __init__(self, system_clean: bool) -> None:
        self.system_clean = system_clean
        self._pkg_managers = [
            pkg_manager(self.system_clean)
            for pkg_manager in [Rpm, Pip, Pipx]
            if pkg_manager(self.system_clean).exists()
        ]

    def get_package_duplicates(self) -> dict[str, list[PackageInfo]]:
        pkgs = []
        pkg_manager_pbar = tqdm(self._pkg_managers)
        for pkg_manager in pkg_manager_pbar:
            pkg_manager_pbar.set_description(f"Processing {pkg_manager.pkg_type.name}")
            pkgs.extend(pkg_manager.get_python_packages())

        dupes_per_package_name = []
        unique = set()
        for pkg in pkgs:
            if pkg.name in unique:
                dupes_per_package_name.append(pkg.name)
            else:
                unique.add(pkg.name)

        result = {name: [] for name in dupes_per_package_name}
        for pkg in pkgs:
            # maybe installed same version via e.g. pip to user-space and system-wide, but
            # then location should be different
            if pkg.name in dupes_per_package_name and (
                result.get(pkg.name) is None or pkg not in result[pkg.name]
            ):
                result[pkg.name].append(pkg)

        return result

    def _input_for_pkg_manager(self) -> PackageManager:
        while True:
            chosen_pkg_manager = input()
            for pkg_manager in self._pkg_managers:
                if pkg_manager.pkg_type.name == chosen_pkg_manager:
                    return pkg_manager

            print("Invalid package manager name.")

    @staticmethod
    def _input_ask_yes_no(msg: str) -> bool:
        while True:
            chosen_auto_remove = input(msg)
            if chosen_auto_remove.lower() in ["y", "n"]:
                return chosen_auto_remove.lower() == "y"

            print("Invalid input.")

    def _interactive_clean_step(
            self, package_name: str, packages_infos: list[PackageInfo]
        ) -> None:
        while True:
            print("Choose one package manager to keep the package (write one of these):")
            for pkg_manager in self._pkg_managers:
                print(f"{pkg_manager.pkg_type.name}")

            chosen_pkg_manager = self._input_for_pkg_manager()
            chosen_auto_remove = self._input_ask_yes_no(
                "Do you want to automatically remove dependencies of the package? [y/N]"
            )

            for pkg_manager in self._pkg_managers:
                if pkg_manager.pkg_type == chosen_pkg_manager.pkg_type:
                    continue

                if not any(
                    pkg_manager.pkg_type == pkg_info.pkg_type
                    for pkg_info in packages_infos
                ):
                    continue

                if not self._input_ask_yes_no(
                    f"\nDo you really want to remove package {package_name} "
                    f"via {pkg_manager.pkg_type}? [y/N]"
                ):
                    return

                pkg_manager.remove_python_package(package_name, chosen_auto_remove)

    def interactive_clean(self) -> None:
        pbar = tqdm(total=1)
        pbar.set_description(f"Getting duplication packages on your system...")
        dupes = self.get_package_duplicates()
        pbar.update(1)

        pbar_interactive = tqdm(dupes.items())
        for pkg_name, pkgs_infos in pbar_interactive:
            pbar_interactive.set_description(f"Cleaning {pkg_name}")
            print(dupe_table(pkg_name, pkgs_infos, verbose=False))
            print("")
            self._interactive_clean_step(pkg_name, pkgs_infos)

    @staticmethod
    def _duplicates_for_pkg_type(
        pkg_type: PkgType, duplicates: dict[str, list[PackageInfo]]
    ) -> set[str]:
        result = set()
        for pkg_name, pkgs in duplicates.items():
            for pkg in pkgs:
                if pkg.pkg_type == pkg_type:
                    result.add(pkg_name)
                    break

        return result

    def clean(self, pkg_type: PkgType, auto_remove: bool) -> None:
        for pkg_manager in self._pkg_managers:
            if pkg_manager.pkg_type != pkg_type:
                continue

            pbar = tqdm(total=2)
            pbar.set_description(f"Getting duplication packages on your system...")
            dupes = self._duplicates_for_pkg_type(
                pkg_manager.pkg_type, self.get_package_duplicates()
            )
            pbar.update(1)
            pbar.set_description(
                f"Removing duplicates for {pkg_manager.pkg_type.name}..."
            )
            pkg_manager.remove_python_packages(dupes, auto_remove)
            pbar.update(1)
