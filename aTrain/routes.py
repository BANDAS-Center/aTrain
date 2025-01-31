import platform

from aTrain_core.globals import (
    DOCUMENTS_DIR,
    MODELS_DIR,
    REQUIRED_MODELS,
    REQUIRED_MODELS_DIR,
    GUI_CONNECTOR,
)
from aTrain_core.load_resources import remove_model
from flask import Blueprint, Response, redirect, render_template, request, url_for
from torch import cuda

from .archive import (
    check_access,
    delete_transcription,
    load_faqs,
    open_file_directory,
    read_archive,
    read_directories,
)
from .models import (
    model_languages,
    read_downloaded_models,
    read_model_metadata,
    start_model_download,
    stop_all_downloads,
)
from .transcription import create_thread, stop_all_transcriptions
from .version import __version__

routes = Blueprint("routes", __name__)


@routes.context_processor
def set_globals():
    return dict(version=__version__)


@routes.get("/")
def home():
    if check_access(DOCUMENTS_DIR):
        models = read_downloaded_models()  # Get the list of downloaded models

        try:
            if REQUIRED_MODELS[1] in models:
                default_model = REQUIRED_MODELS[1]
            elif models:
                default_model = models[
                    0
                ]  # Fall back to the first model if any models are available

            languages = model_languages(default_model)
            return render_template(
                "routes/transcribe.html",
                cuda=cuda.is_available(),
                models=models,
                languages=languages,
                default_model=default_model,  # Pass the default model to the template
            )

        except KeyError:
            default_model = None  # No models available
            languages = {}
            return render_template(
                "routes/transcribe.html",
                cuda=cuda.is_available(),
                models=models,
                languages=languages,
                default_model=default_model,  # Pass the default model to the template
            )
    else:
        return render_template("routes/access_required.html")


@routes.get("/archive")
def archive():
    return render_template("routes/archive.html", archive_data=read_archive())


@routes.get("/faq")
def faq():
    return render_template("routes/faq.html", faqs=load_faqs())


@routes.get("/about")
def about():
    return render_template("routes/about.html")


@routes.get("/model_manager")
def model_manager():
    return render_template(
        "routes/model_manager.html",
        models=read_model_metadata(),
        REQUIRED_MODELS=REQUIRED_MODELS,
    )


@routes.post("/get_num_speakers_on_toggle")
def get_num_speakers_on_toggle():
    is_checked = request.form.get("speaker_detection") == "on"
    selected_speaker_count = request.form.get("num_speakers", "auto-detect")

    return render_template(
        "settings/num_speakers.html",
        visible=is_checked,
        selected_speaker_count=selected_speaker_count,
    )


@routes.route("/get_languages", methods=["GET", "POST"])
def get_languages():
    model = request.form.get("model")
    languages_dict = model_languages(model)
    return render_template("settings/languages.html", languages=languages_dict)


@routes.post("/start_transcription")
def start_transcription():
    create_thread(request)
    return ""


@routes.get("/stop_transcription")
def stop_transcription():
    stop_all_transcriptions()
    return redirect(url_for("routes.home"))


@routes.get("/SSE")
def SSE():
    return Response(GUI_CONNECTOR.stream(), mimetype="text/event-stream")


@routes.get("/open_directory/<file_id>")
def open_directory(file_id):
    open_file_directory(file_id)
    return ""


@routes.get("/open_latest_transcription")
def open_latest_transcription():
    latest_transcription = read_directories()[0]
    open_file_directory(latest_transcription)
    return ""


@routes.get("/delete_directory/<file_id>")
def delete_directory(file_id):
    delete_transcription(file_id)
    return render_template(
        "routes/archive.html", archive_data=read_archive(), only_content=True
    )


@routes.get("/download_model/<model>")
def download_model(model):
    if model in REQUIRED_MODELS and platform.system() == "Linux":
        models_dir = MODELS_DIR
    elif (
        model in REQUIRED_MODELS
        and platform.system() == "Windows"
        or model in REQUIRED_MODELS
        and platform.system() == "Darwin"
    ):
        models_dir = REQUIRED_MODELS_DIR
    else:
        models_dir = MODELS_DIR
    start_model_download(model, models_dir)
    return render_template(
        "routes/model_manager.html",
        models=read_model_metadata(),
        only_content=True,
        REQUIRED_MODELS=REQUIRED_MODELS,
    )


@routes.get("/stop_download")
def stop_download():
    stop_all_downloads()
    return ""


@routes.get("/delete_model/<model>")
def delete_model(model):
    remove_model(model)
    return render_template(
        "routes/model_manager.html",
        models=read_model_metadata(),
        only_content=True,
        REQUIRED_MODELS=REQUIRED_MODELS,
    )
