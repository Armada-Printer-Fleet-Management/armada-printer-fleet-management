from pathlib import Path

import webview


def choose_save_path(suggested_name: str) -> Path | None:
    """The native Save dialog, opened over the app window. None when the user cancels."""
    window = webview.active_window()
    if window is None:
        raise RuntimeError("There is no window to open the save dialog over")
    chosen = window.create_file_dialog(
        webview.FileDialog.SAVE,
        directory=str(Path.home() / "Downloads"),
        save_filename=suggested_name,
        file_types=("Zip archive (*.zip)",),
    )
    if not chosen:
        return None
    # pywebview's annotation says a sequence, but the Windows save dialog returns a plain string.
    return Path(chosen if isinstance(chosen, str) else chosen[0])
