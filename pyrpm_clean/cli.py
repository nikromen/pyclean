import time
from dataclasses import dataclass
from typing import Any

import click
from click import Context, pass_context

from pyrpm_clean.cleaner import Cleaner
from pyrpm_clean.constants import CleanType
from pyrpm_clean.helpers import dupe_table


@dataclass
class Obj:
    cleaner: Cleaner


def _get_context_settings() -> dict[str, Any]:
    return {"help_option_names": ["-h", "--help"]}


@click.group("pyrpm-clean", context_settings=_get_context_settings())
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
    "--clean-type",
    type=click.Choice(CleanType.__members__),
    default=CleanType.pypi,
    show_default=True,
    help="Remove pypi or rpm packages or do it interactively.",
)
@click.option(
    "--autoremove",
    is_flag=True,
    default=False,
    help="Remove dependencies of the packages, works only with RPMs",
)
@pass_context
def clean(ctx: Context, clean_type: CleanType, autoremove: bool) -> None:
    """
    Remove duplicite packages that are present as pip and rpm package.

    This step is not recommended for running for system clean, as manual inspection might be
    needed.
    """
    if ctx.obj.cleaner.system_clean:
        print(
            "System clean is enabled, this operation may remove system packages."
            "Please make sure you know what you are doing."
            "Do you want to continue? [y/N]",
        )
        if input().lower() != "y":
            return

    if clean_type == CleanType.pypi and ctx.obj.cleaner.system_clean:
        print(
            "You are about to remove pypi packages, this operation may remove system packages "
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

    if clean_type == CleanType.rpm:
        print(
            "You are about to remove rpm packages, this operation may remove system packages "
            "and requires manual confirmation for removal or manual intervention."
            "Do you want to continue? [y/N]",
        )
        if input().lower() != "y":
            return

    ctx.obj.cleaner.clean(clean_type, autoremove)


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
    for pkg_name, dupe in ctx.obj.cleaner.get_packages_to_clean().items():
        print(dupe_table(pkg_name, dupe, verbose))


if __name__ == "__main__":
    entry_point()
