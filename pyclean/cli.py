import time
from dataclasses import dataclass
from typing import Any

import click
from click import Context, pass_context

from pyclean.cleaner.cleaner import Cleaner
from pyclean.constants import PkgType
from pyclean.helpers import dupe_table


@dataclass
class Obj:
    cleaner: Cleaner


def _get_context_settings() -> dict[str, Any]:
    return {"help_option_names": ["-h", "--help"]}


@click.group("pyclean", context_settings=_get_context_settings())
@click.option(
    "-s",
    "--system-clean",
    is_flag=True,
    default=False,
    help="Look for packages in the whole system.",
)
@pass_context
def entry_point(ctx: Context, system_clean: bool) -> None:
    """
    Tool to identify/remove packages installed both as rpm and pip.
    """
    ctx.obj = Obj(cleaner=Cleaner(system_clean=system_clean))


@entry_point.command("clean")
@click.option(
    "-t",
    "--package-type",
    type=click.Choice(PkgType.__members__),
    default=None,
    show_default=True,
    help="Clean duplicate python packages from desired package manager.",
)
@click.option(
    "--auto-remove",
    is_flag=True,
    default=False,
    help="Remove dependencies of the packages, works only with RPMs",
)
@click.option(
    "-i",
    "--interactive",
    is_flag=True,
    default=False,
    help="Choose package-type in the process and confirm deletion.",
)
@pass_context
def clean(
    ctx: Context,
    pkg_type: PkgType,
    auto_remove: bool,
    interactive: bool,
) -> None:
    """
    Remove duplicate packages that are present as pip and rpm package.

    Or run in interactive mode, where you will choose clean type and confirm deletion on
    each package. Clean is not recommended for running for system clean, as manual
    inspection might be needed.
    """
    if interactive and (auto_remove or pkg_type is not None):
        print(
            "Interactive mode is enabled, auto-remove and package type options will be ignored.",
        )

    if not interactive and pkg_type is None:
        print("You have to specify package type when not running in interactive mode.")
        return

    if ctx.obj.cleaner.system_clean:
        print(
            "System clean is enabled, this operation may remove system packages."
            "Please make sure you know what you are doing."
            "Do you want to continue? [y/N]",
        )
        if input().lower() != "y":
            return

    if pkg_type in [PkgType.pip, PkgType.pipx] and ctx.obj.cleaner.system_clean:
        print(
            "You are about to remove python packages, this operation may remove system packages "
            "this will probably require running this script as root, which is not recommended."
            "Instead, list the packages you need with --system-clean and then proceed the "
            "removal manually."
            "Do you still want to continue? [y/N]",
        )
        if input().lower() != "y":
            return
        print("As you wish...")
        # to give them a chance to cancel :D
        time.sleep(3)

    if pkg_type == PkgType.rpm:
        print(
            "You are about to remove rpm packages, this operation may remove system packages "
            "and requires manual confirmation for removal or manual intervention."
            "Do you want to continue? [y/N]",
        )
        if input().lower() != "y":
            return

    if interactive:
        ctx.obj.cleaner.interactive_clean()
    else:
        ctx.obj.cleaner.clean(pkg_type, auto_remove, interactive)


@entry_point.command("show")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    show_default=True,
    default=False,
    help="Show more details about package location.",
)
@pass_context
def show(ctx: Context, verbose: bool) -> None:
    """
    Show duplicite packages both as rpm and python packages.
    """
    for pkg_name, dupe in ctx.obj.cleaner.get_package_duplicates().items():
        print(dupe_table(pkg_name, dupe, verbose))


if __name__ == "__main__":
    entry_point()
