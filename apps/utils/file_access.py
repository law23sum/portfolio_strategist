"""
Utility module for accessing local and cloud drives from within Docker containers.

This module provides helper functions to access files mounted from the host system
into Docker containers. All host-mounted directories are available under /host/*
"""

import os
from pathlib import Path
from typing import List, Optional, Union

# Base paths for mounted drives
HOST_BASE = Path("/host")
HOST_HOME = HOST_BASE / "home"
HOST_CLOUDSTORAGE = HOST_BASE / "cloudstorage"
HOST_GOOGLE_DRIVE = HOST_BASE / "googledrive"
HOST_DROPBOX = HOST_BASE / "dropbox"
HOST_ONEDRIVE = HOST_BASE / "onedrive"
HOST_ICLOUD_DRIVE = HOST_BASE / "iclouddrive"
HOST_DOCUMENTS = HOST_BASE / "documents"
HOST_DESKTOP = HOST_BASE / "desktop"
HOST_DOWNLOADS = HOST_BASE / "downloads"


def get_host_path(relative_path: Union[str, Path]) -> Path:
    """
    Convert a relative path from the host home directory to the container mount path.

    Args:
        relative_path: Path relative to the host home directory (e.g., "Documents/file.txt")

    Returns:
        Path object pointing to the mounted location in the container

    Example:
        >>> path = get_host_path("Documents/myfile.txt")
        >>> # Returns: Path("/host/home/Documents/myfile.txt")
    """
    return HOST_HOME / relative_path


def get_cloud_path(cloud_provider: str, relative_path: Union[str, Path] = "") -> Optional[Path]:
    """
    Get the path to a cloud drive mount point.

    Args:
        cloud_provider: One of "googledrive", "dropbox", "onedrive", "iclouddrive", "cloudstorage"
        relative_path: Optional path relative to the cloud drive root

    Returns:
        Path object or None if the cloud provider is not recognized

    Example:
        >>> path = get_cloud_path("googledrive", "MyFolder/file.txt")
        >>> # Returns: Path("/host/googledrive/MyFolder/file.txt")
    """
    cloud_mounts = {
        "googledrive": HOST_GOOGLE_DRIVE,
        "dropbox": HOST_DROPBOX,
        "onedrive": HOST_ONEDRIVE,
        "iclouddrive": HOST_ICLOUD_DRIVE,
        "cloudstorage": HOST_CLOUDSTORAGE,
    }

    base_path = cloud_mounts.get(cloud_provider.lower())
    if base_path is None:
        return None

    if relative_path:
        return base_path / relative_path
    return base_path


def check_access(path: Union[str, Path], check_write: bool = False) -> dict:
    """
    Check file/directory access permissions.

    Args:
        path: Path to check
        check_write: If True, also check write permissions

    Returns:
        Dictionary with access information:
        {
            "exists": bool,
            "readable": bool,
            "writable": bool,
            "executable": bool,
            "is_file": bool,
            "is_dir": bool,
            "size": int (if file),
        }
    """
    path_obj = Path(path)
    result = {
        "exists": path_obj.exists(),
        "readable": False,
        "writable": False,
        "executable": False,
        "is_file": False,
        "is_dir": False,
        "size": 0,
    }

    if not result["exists"]:
        return result

    try:
        stat_info = path_obj.stat()
        result["readable"] = os.access(path_obj, os.R_OK)
        result["writable"] = os.access(path_obj, os.W_OK)
        result["executable"] = os.access(path_obj, os.X_OK)
        result["is_file"] = path_obj.is_file()
        result["is_dir"] = path_obj.is_dir()

        if result["is_file"]:
            result["size"] = stat_info.st_size
    except (OSError, PermissionError) as e:
        result["error"] = str(e)

    return result


def list_directory(path: Union[str, Path], pattern: str = "*") -> List[Path]:
    """
    List files and directories in a given path.

    Args:
        path: Directory path to list
        pattern: Glob pattern to filter files (default: "*")

    Returns:
        List of Path objects

    Raises:
        PermissionError: If access is denied
        NotADirectoryError: If path is not a directory
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return []
    if not path_obj.is_dir():
        raise NotADirectoryError(f"{path} is not a directory")

    if not os.access(path_obj, os.R_OK):
        raise PermissionError(f"Read access denied for {path}")

    return list(path_obj.glob(pattern))


def read_file(path: Union[str, Path], mode: str = "r", encoding: str = "utf-8") -> Union[str, bytes]:
    """
    Read a file from a mounted drive.

    Args:
        path: Path to the file
        mode: File mode ("r" for text, "rb" for binary)
        encoding: Text encoding (only used for text mode)

    Returns:
        File contents as string or bytes

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If access is denied
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path_obj.is_file():
        raise ValueError(f"{path} is not a file")

    if not os.access(path_obj, os.R_OK):
        raise PermissionError(f"Read access denied for {path}")

    if "b" in mode:
        return path_obj.read_bytes()
    else:
        return path_obj.read_text(encoding=encoding)


def write_file(
    path: Union[str, Path],
    content: Union[str, bytes],
    mode: str = "w",
    encoding: str = "utf-8",
    create_dirs: bool = True,
) -> int:
    """
    Write content to a file on a mounted drive.

    Args:
        path: Path to the file
        content: Content to write (string or bytes)
        mode: File mode ("w" for text, "wb" for binary)
        encoding: Text encoding (only used for text mode)
        create_dirs: If True, create parent directories if they don't exist

    Returns:
        Number of bytes written

    Raises:
        PermissionError: If write access is denied
    """
    path_obj = Path(path)

    if create_dirs:
        path_obj.parent.mkdir(parents=True, exist_ok=True)

    if not os.access(path_obj.parent if path_obj.exists() else path_obj.parent, os.W_OK):
        raise PermissionError(f"Write access denied for {path}")

    if "b" in mode:
        if isinstance(content, str):
            content = content.encode(encoding)
        return path_obj.write_bytes(content)
    else:
        if isinstance(content, bytes):
            content = content.decode(encoding)
        return path_obj.write_text(content, encoding=encoding)


def execute_file(path: Union[str, Path], *args) -> Optional[int]:
    """
    Execute a file (script or binary) from a mounted drive.

    Args:
        path: Path to the executable file
        *args: Arguments to pass to the executable

    Returns:
        Exit code or None if execution failed

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If execute access is denied
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not os.access(path_obj, os.X_OK):
        raise PermissionError(f"Execute access denied for {path}")

    import subprocess

    try:
        result = subprocess.run([str(path_obj)] + list(args), check=False)
        return result.returncode
    except Exception as e:
        raise RuntimeError(f"Failed to execute {path}: {e}")


# Convenience functions for common locations
def get_documents_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path to Documents directory."""
    if relative_path:
        return HOST_DOCUMENTS / relative_path
    return HOST_DOCUMENTS


def get_desktop_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path to Desktop directory."""
    if relative_path:
        return HOST_DESKTOP / relative_path
    return HOST_DESKTOP


def get_downloads_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path to Downloads directory."""
    if relative_path:
        return HOST_DOWNLOADS / relative_path
    return HOST_DOWNLOADS
