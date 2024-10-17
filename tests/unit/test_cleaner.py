from unittest.mock import MagicMock, patch

import pytest

from pyclean.cleaner.package_managers.base import PackageInfo
from pyclean.cleaner.package_managers.pip import Pip
from pyclean.cleaner.package_managers.pipx import Pipx
from pyclean.cleaner.package_managers.rpm import Rpm
from pyclean.constants import PkgType
from tests.conftest import (
    package_a_pip,
    package_a_pipx,
    package_a_rpm,
    package_b_pip,
    package_b_pipx,
    package_b_rpm,
)


@pytest.mark.parametrize(
    "rpm_packages, pip_packages, pipx_packages, expected",
    [
        pytest.param(
            [package_a_rpm],
            [package_a_pip],
            [],
            {"package_a": [package_a_rpm, package_a_pip]},
            id="rpm and pip",
        ),
        pytest.param(
            [package_a_rpm],
            [package_b_pip],
            [package_a_pipx],
            {"package_a": [package_a_rpm, package_a_pipx]},
            id="rpm and pipx",
        ),
        pytest.param(
            [package_a_rpm, package_b_rpm],
            [package_a_pip, package_b_pip],
            [package_b_pipx],
            {
                "package_a": [package_a_rpm, package_a_pip],
                "package_b": [package_b_rpm, package_b_pip, package_b_pipx],
            },
            id="rpm, pip, and pipx",
        ),
        pytest.param(
            [package_a_rpm, package_b_rpm],
            [package_a_pip, package_b_pip],
            [],
            {
                "package_a": [package_a_rpm, package_a_pip],
                "package_b": [package_b_rpm, package_b_pip],
            },
            id="rpm and pip 2 dupes",
        ),
        pytest.param([], [], [], {}, id="no packages"),
        pytest.param(
            [package_a_rpm],
            [package_b_pip],
            [
                PackageInfo(
                    name="package_c",
                    package_name="package_c",
                    version="1.0",
                    location="/home/user/.local",
                    pkg_type=PkgType.pipx,
                    files=["file1", "file2"],
                ),
            ],
            {},
            id="no dupes",
        ),
    ],
)
@patch.object(Rpm, "get_python_packages")
@patch.object(Pip, "get_python_packages")
@patch.object(Pipx, "get_python_packages")
def test_get_package_duplicates(
    mock_pipx,
    mock_pip,
    mock_rpm,
    user_cleaner,
    rpm_packages,
    pip_packages,
    pipx_packages,
    expected,
):
    mock_rpm.return_value = rpm_packages
    mock_pip.return_value = pip_packages
    mock_pipx.return_value = pipx_packages
    user_cleaner.get_package_duplicates()

    duplicates = user_cleaner.get_package_duplicates()
    assert duplicates == expected


@patch.object(Rpm, "get_python_packages")
@patch.object(Rpm, "remove_python_packages")
@patch.object(Pip, "get_python_packages")
@patch.object(Pip, "remove_python_packages")
@patch.object(Pipx, "get_python_packages")
@patch.object(Pipx, "remove_python_packages")
def test_clean(
    mock_pipx_remove,
    mock_pipx_get,
    mock_pip_remove,
    mock_pip_get,
    mock_rpm_remove,
    mock_rpm_get,
    user_cleaner,
):
    mock_rpm_get.return_value = [package_a_rpm]
    mock_pip_get.return_value = [package_a_pip]
    mock_pipx_get.return_value = [package_a_pipx]

    mock_rpm_remove.return_value = MagicMock()
    mock_pip_remove.return_value = MagicMock()
    mock_pipx_remove.return_value = MagicMock()

    user_cleaner.clean(PkgType.rpm, False)
    mock_rpm_remove.assert_called_once_with({package_a_rpm.package_name}, False)
    mock_pip_remove.assert_not_called()
    mock_pipx_remove.assert_not_called()


@patch("builtins.input", side_effect=["2", "y", "y"])
@patch.object(Rpm, "get_python_packages")
@patch.object(Rpm, "remove_python_packages")
@patch.object(Pip, "get_python_packages")
@patch.object(Pip, "remove_python_packages")
@patch.object(Pipx, "get_python_packages")
@patch.object(Pipx, "remove_python_packages")
def test_clean_interactive(
    mock_pipx_remove,
    mock_pipx_get,
    mock_pip_remove,
    mock_pip_get,
    mock_rpm_remove,
    mock_rpm_get,
    mock_input,
    user_cleaner,
):
    mock_rpm_get.return_value = [package_a_rpm]
    mock_pip_get.return_value = [package_a_pip]
    mock_pipx_get.return_value = [package_b_pipx]

    mock_rpm_remove.return_value = MagicMock()
    mock_pip_remove.return_value = MagicMock()
    mock_pipx_remove.return_value = MagicMock()

    user_cleaner.interactive_clean()

    mock_rpm_remove.assert_not_called()
    # pip is second in the package_manager list so this should be second package
    mock_pip_remove.assert_called_once_with({package_a_pip.package_name}, True)
    mock_pipx_remove.assert_not_called()
