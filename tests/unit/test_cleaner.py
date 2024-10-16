import pytest
from pyclean.cleaner import Cleaner, PackageInfo
from unittest.mock import patch, MagicMock


@pytest.mark.parametrize(
    "files, expected",
    [
        ("file1\nfile2\nfile3", ["file1", "file2", "file3"]),
        ("file1\nfile2\nfile3\n", ["file1", "file2", "file3"]),
        ("file1\nfile2\nfile3\n\n", ["file1", "file2", "file3"]),
        ("file1\nfile2\nfile3\n\n\n", ["file1", "file2", "file3"]),
    ],
)
@patch("pyclean.cleaner.run")
def test_get_rpm_package_files(mock_run, files, expected):
    mock_run.return_value.stdout = files
    assert Cleaner._get_rpm_package_files("package") == expected
