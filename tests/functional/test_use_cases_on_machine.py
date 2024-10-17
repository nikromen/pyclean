# these tests should run inside clean fedora container otherwise they may fail

# TODO: allow testing for different distros so that we can test for different package managers
# I guess this means containerfile per distro with configuration of these PMs
from subprocess import run

from pyclean.cleaner.cleaner import Cleaner


def test_get_package_duplicates():
    cleaner = Cleaner(system_clean=False)
    pkgs = cleaner.get_package_duplicates()
    assert pkgs == {}

    run("dnf install -y pip pipx")
    pkgs = cleaner.get_package_duplicates()
    # nothing is installed via pip or pipx still
    assert pkgs == {}

    run("dnf install python3-fastapi")
    pkgs = cleaner.get_package_duplicates()
    # nothing is installed via pip or pipx still
    assert pkgs == {}

    run("pip install fastapi")
    pkgs = cleaner.get_package_duplicates()
    assert "fastapi" in pkgs
    assert len(pkgs["fastapi"]) == 2

    run("pipx install fastapi")
    pkgs = cleaner.get_package_duplicates()
    assert "fastapi" in pkgs
    assert len(pkgs["fastapi"]) == 3

    run("pip uninstall fastapi")
    pkgs = cleaner.get_package_duplicates()
    assert "fastapi" in pkgs
    assert len(pkgs["fastapi"]) == 2

    run("pipx uninstall fastapi")
    pkgs = cleaner.get_package_duplicates()
    assert pkgs == {}
