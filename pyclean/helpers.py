from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyclean.cleaner.cleaner import PackageInfo


def dupe_table(
    name: str,
    package_dupes: list[PackageInfo],
    verbose: bool = False,
) -> str:
    """
    Create a table with duplicite packages.
    """
    table_delimiter = "  | " + "-" * 124 + " |"
    main_delimiter = "=" * 130
    table = [
        main_delimiter,
        "",
        f"Name: {name}",
        "Duplicities found:",
        "  | {:<55} {:<20} {:<15} {:<15} {:<15} |".format(
            "Location",
            "Package full name",
            "Version",
            "Installer",
            "Files count",
        ),
        table_delimiter,
    ]
    for dupe in package_dupes:
        installer_type = dupe.pkg_type.name if dupe.pkg_type else "unknown"
        table.append(
            f"  | {dupe.location: <55} {dupe.package_name: <20} {dupe.version: <15} "
            f"{installer_type: <15} {len(dupe.files): <15} |",
        )
        if not verbose:
            continue

        table.append("  | Files:" + " " * 113 + " |")
        for file in dupe.files:
            table.append(f"  |   {file:<117} |")

        table.append(table_delimiter)

    table.append("")
    table.append(main_delimiter)
    return "\n".join(table)
