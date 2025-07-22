import sys
import threading
from pathlib import Path

# Start Dash server in the background -----------------------------
from dashboard.root import start_server  # ⚠️ your Dash app factory

# Qt imports ------------------------------------------------------
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView

# Qt >= 6.5 moved the download class into QtWebEngineCore
# Fall‑back to the old location so one file works on both Qt 5 & Qt 6
try:
    from PySide6.QtWebEngineCore import QWebEngineDownloadRequest  # Qt 6.5+
except ImportError:  # Qt 5 / early Qt 6
    from PySide6.QtWebEngineWidgets import (
        QWebEngineDownloadItem as QWebEngineDownloadRequest,
    )

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
    # Spin up Dash in a daemon thread so Qt owns the m
    # ain loop
    threading.Thread(target=start_server, daemon=False).start()

    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(qt_app.exec())
