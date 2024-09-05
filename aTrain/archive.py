import os
import shutil
from importlib.resources import files

import yaml
from aTrain_core.globals import METADATA_FILENAME, TRANSCRIPT_DIR
from showinfm import show_in_file_manager


def read_archive() -> list:
    """A function that reads all past transcriptions still located in the archive."""
    all_directories = read_directories()
    all_metadata = read_all_metadata(all_directories)
    return all_metadata


def read_directories() -> list:
    """A function that returns a list of all directories in the archive folder"""
    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
    directories = [
        directory.name for directory in os.scandir(TRANSCRIPT_DIR) if directory.is_dir()
    ]
    directories.sort(reverse=True)
    return directories


def read_all_metadata(all_directories) -> list:
    """A function that returns all available metadata from past transcriptions"""
    all_metadata = []
    for directory in all_directories:
        metadata_file_path = os.path.join(TRANSCRIPT_DIR, directory, METADATA_FILENAME)
        if os.path.exists(metadata_file_path):
            metadata = read_metadata_file(metadata_file_path, directory)
        else:
            metadata = read_metadata_from_dir_name(directory)
        all_metadata.append(metadata)
    return all_metadata


def read_metadata_file(metadata_file_path, directory) -> dict:
    """A function that reads the content of a metadata file for a given transcription."""
    with open(metadata_file_path, "r", encoding="utf-8") as metadata_file:
        metadata: dict = yaml.safe_load(metadata_file)
        metadata["file_id"] = directory
    return metadata


def read_metadata_from_dir_name(directory) -> dict:
    """A function that extracts metadata from the directory name in the archive."""
    metadata = {
        "file_id": directory,
        "filename": directory[20:] if len(directory) > 20 else "-",
        "timestamp": directory[:20] if len(directory) >= 20 else "-",
    }
    return metadata


def delete_transcription(file_id) -> None:
    """A function that deletes a past transcription form the archive."""
    file_id = "" if file_id == "all" else file_id
    directory = os.path.join(TRANSCRIPT_DIR, file_id)
    if os.path.exists(directory):
        shutil.rmtree(directory)
    if not os.path.exists(TRANSCRIPT_DIR):
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)


def open_file_directory(file_id) -> None:
    """A function that opens the output from a past transcription in the file explorer."""
    file_id = "" if file_id == "all" else file_id
    directory = os.path.join(TRANSCRIPT_DIR, file_id)
    if os.path.exists(directory):
        show_in_file_manager(directory)


def load_faqs() -> dict:
    """A function that reads the content of the faq file."""
    faq_path = str(files("aTrain.static").joinpath("faq.yaml"))
    with open(faq_path, "r", encoding="utf-8") as faq_file:
        faqs: dict = yaml.safe_load(faq_file)
    return faqs


def check_access(path: str) -> bool:
    """Check if the application has access to the given path."""
    try:
        # Check if the directory exists and is readable
        if os.path.isdir(path):
            return len(os.listdir(path)) >= 0
        else:
            with open(path, "r") as f:
                f.read()
        return True
    except PermissionError:
        return False
    except FileNotFoundError:
        return False


def show_permission_instructions() -> None:
    """Show a message box with instructions for granting permissions."""
    print(
        "Access Required",
        "This application needs access to the Documents folder. Please grant this access in System Preferences > Security & Privacy > Privacy > Files and Folders.",
    )
