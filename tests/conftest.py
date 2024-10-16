import pytest

from cleaner import Cleaner, PackageInfo


@pytest.fixture
def user_cleaner():
    return Cleaner(system_clean=False)


@pytest.fixture
def system_cleaner():
    return Cleaner(system_clean=True)
