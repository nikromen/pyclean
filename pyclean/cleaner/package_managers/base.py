from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from pyclean.constants import PkgType


@dataclass
class PackageInfo:
    name: str
    # some package managers like rpm may have python3- prefix for libraries
    # and no prefix for executables
    package_name: str
    version: str
    location: Optional[str]
    files: list[str]
    pkg_type: Optional[PkgType] = None


class PackageManager(ABC):
    def __init__(self, system_clean: bool) -> None:
        self.system_clean = system_clean
        self.pkg_type = None

    @abstractmethod
    def get_python_packages(self) -> list[PackageInfo]:
        """
        Get all installed Python packages on the system via specific package manager.
        """
        ...

    @abstractmethod
    def remove_python_packages(self, packages: set[str], auto_remove: bool) -> None:
        """
        Remove Python packages from the system via specific package manager.

        Args:
            packages: Set of package names to remove.
            auto_remove: Whether to automatically remove dependencies of the packages.
        """
        ...

    @abstractmethod
    def exists(self) -> bool:
        """
        Check if package manager exists on the system.
        """
        ...

    def remove_python_package(self, package: str, auto_remove: bool) -> None:
        """
        Remove single Python package from the system via specific package manager.

        Args:
            package: Single package name to remove.
            auto_remove: Whether to automatically remove dependencies of the package.
        """
        self.remove_python_packages({package}, auto_remove)
