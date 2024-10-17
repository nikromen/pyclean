# pyclean

**pyclean** is a tool designed to detect and remove duplicate Python packages installed using
multiple package managers, such as **pip**, **pipx**, **rpm**, and more. This tool simplifies
the process of identifying duplicate python packages that may break your system.

## Why?

Have you installed some Python package using multiple package managers (dnf, pip, pipx, ...),
because you forgot you already installed it via something else? Or you were just lazy enough to
not create a virtual environment and installed the package to user space and forgot about it?
And now over time you have multiple versions of the same package installed? This tool can detect
this!

## Features

- **Duplicate Package Detection:** The tool scans your system and provides a list of Python
  duplicite packages that have been installed via multiple package managers.
- **Duplicate Display:** If the user prefers not to delete any packages, they can simply view
  a list of installed duplicates.
- **Interactive Mode:** Allows users to select which package manager to retain for a given
  package, and automatically removes the duplicates from other package managers.
- **Automatic cleanup:** **WARNING: This feature is experimental and may break your system.**
  This feature allows the user to automatically remove all duplicate packages from the system,
  keeping only the packages installed via the package manager of their choice.

## Installation

### pip

```bash
pip install pyclean
```

### Linux

#### Fedora and EPEL 9

```bash
sudo dnf copr enable nikromen/pyclean
sudo dnf install pyclean
```

## Usage

### Displaying Duplicates

If you prefer just to check which packages have duplicates across different package managers, the
tool will present a detailed overview without performing any removal actions.

### Interactive Mode

After starting the tool, it will display a list of duplicate Python packages installed via
different package managers. Users can:

- Select which package manager they want to keep the package in, and the tool will remove the
  duplicates from other managers.
- Automatically remove the dependencies of the package if chosen.
- Confirm or cancel the removal of the package.

### Automatic cleanup

**WARNING: This feature is experimental and may break your system.**

If you are confident that you want to remove all duplicate packages from your system, you can use
the automatic cleanup feature. This feature will remove all duplicate packages from your system,
keeping only the packages installed via the package manager of your choice.

## Contributing

Contributions are welcome! If you'd like to improve this tool, feel free to open a pull request
or report any issues in the Issues section.
