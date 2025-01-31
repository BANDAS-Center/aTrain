import os
import traceback
import urllib.error
import urllib.request

from aTrain_core.globals import (
    MODELS_DIR,
    REQUIRED_MODELS,
    REQUIRED_MODELS_DIR,
    GUI_CONNECTOR,
)
from aTrain_core.load_resources import (
    get_model,
    load_model_config_file,
    remove_model,
    load_languages_file,
)
from showinfm import show_in_file_manager

from .transcription import StoppableThread

RUNNING_DOWNLOADS = []


def read_downloaded_models() -> list:
    directories_to_search = [MODELS_DIR, REQUIRED_MODELS_DIR]
    all_downloaded_models = []

    for directory in directories_to_search:
        os.makedirs(directory, exist_ok=True)
        all_file_directories = [
            dir_entry.name for dir_entry in os.scandir(directory) if dir_entry.is_dir()
        ]
        all_file_directories.sort(reverse=True)

        for directory_name in all_file_directories:
            directory_path = os.path.join(directory, directory_name)
            for file in os.listdir(directory_path):
                # model only with .bin file available
                if file.endswith(".bin") and directory_name in list(
                    load_model_config_file().keys()
                ):
                    all_downloaded_models.append(directory_name)
                    break

    return all_downloaded_models


def read_model_metadata() -> list:
    model_metadata = load_model_config_file()
    all_models = list(model_metadata.keys())
    downloaded_models = read_downloaded_models()
    all_models_metadata = []

    for model in all_models:
        model_info = {
            "model": model,
            "size": model_metadata[model]["model_bin_size_human"],
            "downloaded": model in downloaded_models,
        }
        all_models_metadata.append(model_info)

    all_models_metadata = sorted(
        all_models_metadata, key=lambda x: x["downloaded"], reverse=True
    )

    return all_models_metadata


def model_languages(model: str) -> dict:
    languages = load_languages_file()
    models = load_model_config_file()

    if models[model]["type"] == "distil":
        lang_from_config = models[model]["language"]
        languages = {lang_from_config: languages[lang_from_config]}

    return languages


def open_model_dir(model: str, models_dir=MODELS_DIR) -> None:
    """A function that opens the directory where a given model is stored."""
    model = "" if model == "all" else model
    directory_name = os.path.join(models_dir, model)
    if os.path.exists(directory_name):
        show_in_file_manager(directory_name)


def start_model_download(model: str, models_dir=MODELS_DIR) -> None:
    """A function that starts the download of a model in a separate process."""
    if model in REQUIRED_MODELS:
        models_dir = REQUIRED_MODELS_DIR

    model_download = StoppableThread(
        target=try_to_download_model,
        kwargs={"model": model, "models_dir": models_dir},
        daemon=True,
    )
    model_download.start()
    RUNNING_DOWNLOADS.append((model_download, model))
    model_download.join()
    RUNNING_DOWNLOADS.remove((model_download, model))


def try_to_download_model(model: str, models_dir=None) -> None:
    """A function that tries to download the specified model and sends any occurring errors to the frontend."""

    if models_dir is None:
        models_dir = MODELS_DIR
    try:
        check_internet()
        get_model(model, models_dir, REQUIRED_MODELS_DIR)
        GUI_CONNECTOR.update_finished()
    except Exception as error:
        traceback_str = traceback.format_exc()
        GUI_CONNECTOR.update_error(str(error), traceback_str)
        remove_model(model)


def check_internet():
    """A function to check whether the user is connected to the internet."""
    try:
        urllib.request.urlopen("https://huggingface.co", timeout=1)
    except urllib.error.URLError:
        raise ConnectionError(
            "We cannot reach Hugging Face. Most likely you are not connected to the internet."
        )


def stop_all_downloads() -> None:
    """A function that terminates all running download processes."""
    download: StoppableThread
    for download, model in RUNNING_DOWNLOADS:
        download.stop()
        download.join()
        remove_model(model)
    RUNNING_DOWNLOADS.clear()
    GUI_CONNECTOR.update_finished()
