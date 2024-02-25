import click
from click import pass_context, Context

from pyrpm_clean.cleaner import Cleaner
from pyrpm_clean.constants import PkgType


@click.group()
@click.option(
    "-u",
    "--user-clean",
    is_flag=True,
    show_default=True,
    default=True,
    help="Look only for pip packages in user-space",
)
@pass_context
def entry_point(ctx: Context, user_clean: bool) -> None:
    ctx.obj = Cleaner(user_clean=user_clean)


@entry_point.command("clean")
@click.option(
    "-t",
    "--clean-type",
    type=PkgType,
    default=PkgType.pypi,
    show_default=True,
    help="Remove pypi or rpm packages",
)
@pass_context
def clean(ctx: Context, clean_type: PkgType) -> None:
    """
    Remove duplicite packages that are present as python package and as rpm package.
    """
    ctx.obj.clean(clean_type)


@entry_point.command("show")
@pass_context
def show(ctx: Context) -> None:
    """
    Show duplicite packages both as rpm and python packages.
    """
    print(ctx.obj.get_packages_to_clean())


if __name__ == "__main__":
    entry_point()
