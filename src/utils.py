# Standard library imports
import errno
import logging
import os
import shutil
import time

# Reader imports
from src.config import ENABLE_OLD_EXPORTS_CLEANUP, OLD_EXPORTS_CLEANUP_DAYS


def cleanup_old_exports(base_export_dir, days):
    """
    Removes directories in the base export directory that are older than the specified number of days.
    """
    now = time.time()
    cutoff_time = now - (days * 86400)  # days to seconds

    for dirpath, dirnames, filenames in os.walk(base_export_dir):
        # Remove old files
        for filename in filenames:
            file_full_path = os.path.join(dirpath, filename)
            if (
                os.path.isfile(file_full_path)
                and os.path.getmtime(file_full_path) < cutoff_time
            ):
                os.remove(file_full_path)
                logging.info(f"Removed old export file: {file_full_path}")

        # Remove old directories
        for dirname in dirnames:
            dir_full_path = os.path.join(dirpath, dirname)
            if (
                os.path.isdir(dir_full_path)
                and os.path.getmtime(dir_full_path) < cutoff_time
            ):
                shutil.rmtree(dir_full_path)
                logging.info(f"Removed old export directory: {dir_full_path}")


def create_working_dir(working_dir):
    """
    Creates a working directory for exports. If cleanup is enabled, it first removes old directories.
    """
    base_export_working_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(working_dir))
    )  # Get the grandparent directory , because exportdir/uid/export
    # Check if cleanup is enabled
    cleanup_enabled = ENABLE_OLD_EXPORTS_CLEANUP
    cleanup_days = OLD_EXPORTS_CLEANUP_DAYS

    if cleanup_enabled:
        cleanup_old_exports(base_export_working_dir, cleanup_days)

    if not os.path.exists(working_dir):
        try:
            os.makedirs(working_dir)
        except OSError as e:
            if e.errno == errno.ENOSPC:  # No space left on device
                logging.warning(
                    "No space left on device, attempting to cleanup old exports and retry..."
                )
                cleanup_old_exports(base_export_working_dir, cleanup_days)
                os.makedirs(working_dir)
            else:
                raise e
    return working_dir
