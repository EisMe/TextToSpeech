"""Detection of optional third-party dependencies.

pydub / PyPDF2 / python-docx are all optional: the app degrades gracefully
without them (no playback, no PDF/DOCX import). Isolating the detection here
means the rest of the codebase only ever imports the resulting HAS_* flags
and never needs to know how the detection itself works.
"""


def safe_import(module_name, package_name=None):
    """Import an optional dependency, returning None if it isn't installed."""
    try:
        if package_name:
            return __import__(module_name, fromlist=[package_name])
        return __import__(module_name)
    except ImportError:
        return None


pydub = safe_import('pydub')
PyPDF2 = safe_import('PyPDF2')
docx = safe_import('docx')

HAS_PYDUB = pydub is not None
HAS_PDF = PyPDF2 is not None
HAS_DOCX = docx is not None