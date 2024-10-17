import json
from pathlib import Path
from subprocess import PIPE, run
from typing import Optional

from tqdm import tqdm

from pyclean.cleaner.package_managers.base import PackageInfo, PackageManager
from pyclean.constants import PkgType


class Pipx(PackageManager):
    def __init__(self, system_clean: bool) -> None:
        super().__init__(system_clean)
        self.pkg_type = PkgType.pipx

    def _pipx_location(self, pkg: dict) -> Optional[Path]:
        # just best effort, it may not work for all cases
        try:
            return Path(pkg["app_paths"][0]["__Path__"]).parent.parent
        except (IndexError, KeyError) as e:
            print(f"Error: {e}")
            return None

    def _pipx_files(self, metadata: dict, pkg_name: str, location: Path) -> list[str]:
        # this is just best effort, it may not work for all cases
        try:
            lib = location / "lib"
            python_lib_name = Path(metadata["source_interpreter"]["__Path__"]).name
            guessed_lib_path = lib / python_lib_name
            if guessed_lib_path.exists():
                return [
                    str(path)
                    for path in (guessed_lib_path / "site-packages" / pkg_name).rglob(
                        "*.py",
                    )
                ]

            for dir_name in lib.iterdir():
                if dir_name.is_dir() and dir_name.name.startswith("python"):
                    return [
                        str(path)
                        for path in (dir_name / "site-packages" / pkg_name).rglob(
                            "*.py",
                        )
                    ]

            return []
        except (IndexError, KeyError) as e:
            print(f"Error: {e}")
            return []

    def get_python_packages(self) -> list[PackageInfo]:
        result = []
        process_stdout = run(
            ["pipx", "list", "--json"],
            stdout=PIPE,
            check=True,
            text=True,
        ).stdout.strip()
        pipx_list_json = json.loads(process_stdout)
        venvs = pipx_list_json["venvs"]
        for _, pkg in tqdm(venvs.items(), desc="Processing pipx packages"):
            metadata = pkg["metadata"]
            pkg = metadata["main_package"]
            pkg_name = pkg["package"]

            tqdm.write(f"Processing pipx package: {pkg_name}")

            location = self._pipx_location(pkg)
            files = []
            if location is not None:
                files = self._pipx_files(metadata, pkg_name, location)

            result.append(
                PackageInfo(
                    name=pkg_name,
                    package_name=pkg_name,
                    version=pkg["package_version"],
                    location=str(location),
                    files=files,
                    pkg_type=PkgType.pipx,
                ),
            )

        return result

    def remove_python_packages(self, packages: set[str], auto_remove: bool) -> None:
        _ = auto_remove
        run(["pipx", "uninstall", *packages])

    def exists(self) -> bool:
        return run(["which", "pipx"], stdout=PIPE).returncode == 0
