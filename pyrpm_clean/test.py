import pipx
from pipx.pipx_metadata_file import PipxMetadata

def list_pipx_packages():
    # Cesta k nainstalovaným virtuálním prostředím (standardní umístění pipx)
    installed_envs = pipx.get_venvs()

    packages = []

    for package, venv_path in installed_envs.items():
        # Metadata o balíčku
        metadata = PipxMetadata(venv_path)

        if metadata.is_valid():
            package_info = {
                "package": package,
                "version": metadata.python_version,
                "python_version": metadata.python_version,
                "files": metadata.
            }
            packages.append(package_info)

    return packages

# Použití funkce
packages = list_pipx_packages()
for pkg in packages:
    print(f"Package: {pkg['package']}, Version: {pkg['version']}, Python: {pkg['python_version']}")
    print(f"Binaries: {', '.join(pkg['binary_paths'])}")
