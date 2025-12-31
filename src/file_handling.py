import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _describe_path_type(p: Path) -> str:
    """Return a human-readable description of a filesystem object's type."""
    if p.is_symlink():
        return "symbolic link"
    if p.is_socket():
        return "socket"
    if p.is_fifo():
        return "FIFO / named pipe"
    if p.is_block_device():
        return "block device"
    if p.is_char_device():
        return "character device"
    return "unknown filesystem object"


def resolve_file_paths(path_string: str, project_root: Path) -> list[Path]:
    """
    Resolve file or directory paths that may be absolute or relative.

    Supports comma-separated paths. Each path can be:
    - A single file: returns that file
    - A directory: returns all files within it (non-recursive)
    - Multiple comma-separated paths: returns all resolved files

    Args:
    path_string: Comma-separated file or directory path string(s) to resolve
    project_root: The project root directory for resolving relative paths

    Returns:
    List of resolved absolute Path objects

    Raises:
    FileNotFoundError: If any resolved path does not exist
    ValueError: If any path is a directory but contains no files

    """
    all_files: list[Path] = []

    for path_segment in path_string.split(","):
        path_segment_cleaned = path_segment.strip()
        if not path_segment_cleaned:
            continue

        input_path = Path(path_segment_cleaned)
        resolved_path = input_path.resolve() if input_path.is_absolute() else (project_root / input_path).resolve()

        if not resolved_path.exists():
            error_msg = f"Path at {resolved_path!s} does not exist."
            raise FileNotFoundError(error_msg)

        if resolved_path.is_file():
            logger.info("File upload path determined to be: %s", resolved_path)
            all_files.append(resolved_path)
        elif resolved_path.is_dir():
            files = [f for f in resolved_path.iterdir() if f.is_file()]
            if not files:
                error_msg = f"Directory at {resolved_path!s} contains no files."
                raise ValueError(error_msg)
            logger.info("Directory upload path determined to be: %s (contains %d files)", resolved_path, len(files))
            for file in files:
                logger.info("  - %s", file.name)
            all_files.extend(files)
        else:
            error_msg = f"Path at {resolved_path!s} is neither a file nor a directory. Filesystem object type: {_describe_path_type(resolved_path)}"
            raise ValueError(error_msg)

    return all_files
