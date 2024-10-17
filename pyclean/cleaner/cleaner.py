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

    def _input_for_package(self, package_infos: list[PackageInfo]) -> PackageInfo:
        while True:
            chosen_pkg_index = input()
            if chosen_pkg_index.isdigit():
                chosen_pkg_index_i = int(chosen_pkg_index)
                if 1 <= chosen_pkg_index_i <= len(package_infos):
                    return package_infos[chosen_pkg_index_i - 1]

            print("Invalid package number.")

    @staticmethod
    def _input_ask_yes_no(msg: str) -> bool:
        while True:
            chosen_auto_remove = input(msg)
            if chosen_auto_remove.lower() in ["y", "n"]:
                return chosen_auto_remove.lower() == "y"

            print("Invalid input.")

    def _interactive_clean_step(self, package_name: str, packages_infos: list[PackageInfo]) -> None:
        package_infos_copy = packages_infos.copy()
        while len(package_infos_copy) > 1:
            print(dupe_table(package_name, package_infos_copy, verbose=False))
            print("Choose package for removal (write the number of the package above):")

            chosen_pkg = self._input_for_package(package_infos_copy)
            chosen_auto_remove = self._input_ask_yes_no(
                "Do you want to automatically remove dependencies of the package "
                f"{chosen_pkg.name}? [y/N]"
            )

            if not self._input_ask_yes_no(
                f"\nDo you really want to remove package {chosen_pkg.name} "
                f"via {chosen_pkg.pkg_type}? [y/N]"
            ):
                return

            for pkg_manager in self._pkg_managers:
                if pkg_manager.pkg_type == chosen_pkg.pkg_type:
                    pkg_manager.remove_python_package(
                        chosen_pkg.name, chosen_auto_remove
                    )

            package_infos_copy.remove(chosen_pkg)

    def interactive_clean(self) -> None:
        pbar = tqdm(total=1)
        pbar.set_description(f"Getting duplication packages on your system...")
        dupes = self.get_package_duplicates()
        pbar.update(1)

        pbar_interactive = tqdm(dupes.items())
        for pkg_name, pkgs_infos in pbar_interactive:
            pbar_interactive.set_description(f"Cleaning {pkg_name}")
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
