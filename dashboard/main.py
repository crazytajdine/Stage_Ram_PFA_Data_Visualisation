import sys, threading
from dashboard.root import start_server  # ← your Dash() lives here now

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Dash Desktop App")
        self.resize(1024, 768)
        webview = QWebEngineView(self)
        webview.load(QUrl("http://127.0.0.1:8050"))
        self.setCentralWidget(webview)


if __name__ == "__main__":
    dash_thread = threading.Thread(target=start_server, daemon=True)
    dash_thread.start()

    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(qt_app.exec())
