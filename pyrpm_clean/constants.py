from enum import StrEnum


class PkgType(StrEnum):
    pip = "pip"
    rpm = "rpm"
    pipx = "pipx"


class CleanType(StrEnum):
    pip = "pip"
    rpm = "rpm"
    pipx = "pipx"
    interactive = "interactive"
