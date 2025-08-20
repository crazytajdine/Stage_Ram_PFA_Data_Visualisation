import sys
import threading
from pathlib import Path

# Start Dash server in the background -----------------------------
from configurations.log_config import init_log
from root import start_server  # ⚠️ your Dash app factory

# Qt imports ------------------------------------------------------
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView


from configurations.config import get_base_config


# Qt >= 6.5 moved the download class into QtWebEngineCore
# Fall‑back to the old location so one file works on both Qt 5 & Qt 6

from PySide6.QtWebEngineCore import QWebEngineDownloadRequest  # Qt 6.5+

from PySide6.QtCore import QUrl


# ---------------------------------------------------------------
# Main window embeds the Dash app and forces downloads to ~/Downloads
# ---------------------------------------------------------------


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard Desktop")
        self.resize(1200, 800)

        self.webview = QWebEngineView(self)
        self.webview.load(QUrl("http://127.0.0.1:8050"))
        self.setCentralWidget(self.webview)

        # Connect ONE handler to catch *all* downloads (CSV, PNG, …)
        profile = self.webview.page().profile()
        profile.downloadRequested.connect(self._handle_download)

    # -----------------------------------------------------------
    # Download handler — works for both the new & legacy APIs
    # -----------------------------------------------------------
    def _handle_download(self, rq: QWebEngineDownloadRequest):
        """Save every browser download straight into ~/Downloads without a dialog."""
        dl_dir = Path.home() / "Downloads"
        dl_dir.mkdir(exist_ok=True)

        # Qt 6.5+ API ---------------------------------------------------
        if hasattr(rq, "setDownloadDirectory"):
            rq.setDownloadDirectory(str(dl_dir))
            # rq.setDownloadFileName("custom_name.ext")  # ← optional override
            rq.accept()
        # Legacy API (Qt 5 / early Qt 6) -------------------------------
        else:
            target_path = dl_dir / rq.downloadFileName()
            rq.setPath(str(target_path))
            rq.accept()

        print(f"⬇️  Download started → {dl_dir / rq.downloadFileName()}")


# ---------------------------------------------------------------
# Bootstrap Qt application ---------------------------------------
# ---------------------------------------------------------------
if __name__ == "__main__":

    config = get_base_config()
    log_file = config.get("log", {}).get(
        "log_file_desktop_app", "logs/dashboard_desktop_app.log"
    )

    init_log(log_file)

    threading.Thread(target=start_server, args=(False,), daemon=True).start()

    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(qt_app.exec())
