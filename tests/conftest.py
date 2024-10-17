import pytest

from pyclean.cleaner.cleaner import Cleaner
from pyclean.cleaner.package_managers.base import PackageInfo
from pyclean.constants import PkgType

package_a_rpm = PackageInfo(
    name="package_a",
    package_name="python3-package_a",
    version="1.0",
    location="/usr/lib",
    pkg_type=PkgType.rpm,
    files=["file1", "file2"],
)


package_a_pip = PackageInfo(
    name="package_a",
    package_name="package_a",
    version="1.1",
    location="/home/user/.local",
    pkg_type=PkgType.pip,
    files=["file1", "file2", "file3"],
)


package_a_pipx = PackageInfo(
    name="package_a",
    package_name="package_a",
    version="1.1.1",
    location="/home/user/.local",
    pkg_type=PkgType.pipx,
    files=["file1", "file2", "file3", "file4"],
)


package_b_rpm = PackageInfo(
    name="package_b",
    package_name="python3-package_b",
    version="1.0",
    location="/usr/lib",
    pkg_type=PkgType.rpm,
    files=["file1", "file2"],
)


package_b_pip = PackageInfo(
    name="package_b",
    package_name="package_b",
    version="1.1",
    location="/home/user/.local",
    pkg_type=PkgType.pip,
    files=["file1", "file2", "file3"],
)


package_b_pipx = PackageInfo(
    name="package_b",
    package_name="package_b",
    version="1.1.1",
    location="/home/user/.local",
    pkg_type=PkgType.pipx,
    files=["file1", "file2", "file3", "file4"],
)


@pytest.fixture
def user_cleaner():
    return Cleaner(system_clean=False)


@pytest.fixture
def system_cleaner():
    return Cleaner(system_clean=True)
