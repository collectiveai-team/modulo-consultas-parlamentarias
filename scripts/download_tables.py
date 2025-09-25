#!/usr/bin/env python3
"""
Script to download tables.tar.xz from Google Drive and extract it to resources/data/tables
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from modulo_consultas_parlamentarias.logger import get_logger

logger = get_logger(__name__)


def download_from_gdrive(file_id: str, output_path: str) -> bool:
    """
    Download a file from Google Drive using gdown.

    Args:
        file_id (str): Google Drive file ID or URL
        output_path (str): Path where to save the downloaded file

    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        subprocess.run(
            ["gdown", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        # Use gdown to download the file
        cmd = ["gdown", "--fuzzy", file_id, "-O", output_path]
        logger.info(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        # Verify file was downloaded
        if not os.path.exists(output_path):
            logger.error(f"Failed to download to {output_path}")
            return False

        return True
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return False


def extract_tar_xz(tar_path: str, extract_to: str) -> bool:
    """
    Extract a .tar.xz file to a directory.

    Args:
        tar_path (str): Path to the .tar.xz file
        extract_to (str): Directory to extract to

    Returns:
        bool: True if extraction was successful, False otherwise
    """
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(extract_to, exist_ok=True)

        # Extract the tar.xz file
        cmd = ["tar", "-xf", tar_path, "-C", extract_to]
        print(f"Extracting {tar_path} to {extract_to}")
        subprocess.run(cmd, check=True)

        return True
    except Exception as e:
        print(f"Error extracting file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download tables.tar.xz from Google Drive and extract it"
    )
    parser.add_argument(
        "--url",
        default="https://drive.google.com/file/d/1Enq1ESgGIm_DXw6cNk3SpkpevqBLwdcL/view",
        help="Google Drive URL or file ID for tables.tar.xz",
    )
    parser.add_argument(
        "--output-dir",
        default="resources/data",
        help="Directory where to extract tables (default: resources/data)",
    )
    args = parser.parse_args()

    # Get the absolute path to the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Download to a temporary file
    with tempfile.NamedTemporaryFile(
        suffix=".tar.xz", delete=False
    ) as temp_file:
        temp_path = temp_file.name

    try:
        logger.info(f"Downloading tables.tar.xz from Google Drive...")
        if download_from_gdrive(args.url, temp_path):
            logger.info("Download successful!")

            # Extract the file
            if extract_tar_xz(temp_path, str(output_dir)):
                logger.info(
                    f"Successfully extracted tables to {output_dir}/tables/"
                )
                return 0

        logger.error("Failed to download or extract the tables archive.")
        return 1
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == "__main__":
    sys.exit(main())
