from enum import StrEnum


class PkgType(StrEnum):
    pypi = "pypi"
    rpm = "rpm"


class CleanType(StrEnum):
    pypi = "pypi"
    rpm = "rpm"
    interactive = "interactive"
