from enum import StrEnum


class PkgType(StrEnum):
    pip = "pip"
    rpm = "rpm"
    pipx = "pipx"
