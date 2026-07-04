"""Small app-wide constants and one-time environment/filesystem setup.

setup_temp_dir() is a plain function, not a module-level side effect, so
importing this module never touches the filesystem or os.environ on its own
-- that only happens when main() explicitly calls it.
"""
import os

AUDIO_FILE_NAME = "georgian_audio.wav"
AUDIO_FORMAT = "wav"


def setup_temp_dir() -> str:
    """Create (if needed) and register the app's own temp directory.

    Call this once from main(), before creating the QApplication.
    """
    custom_temp = os.path.join(os.getcwd(), "my_temp")
    os.makedirs(custom_temp, exist_ok=True)
    os.environ["TEMP"] = custom_temp
    os.environ["TMP"] = custom_temp
    return custom_temp