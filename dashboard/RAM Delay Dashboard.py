import threading
import webview

from configurations.log_config import init_log
from root import start_server  # ⚠️ your Dash app factory
from configurations.config import get_base_config


# ---------------------------------------------------------------
# Download handling
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# Bootstrap pywebview application
# ---------------------------------------------------------------
if __name__ == "__main__":
    config = get_base_config()
    log_file = config.get("log", {}).get(
        "log_file_desktop_app", "logs/dashboard_desktop_app.log"
    )
    init_log(log_file)

    # Start Dash server in a background thread
    threading.Thread(target=start_server, args=(False,), daemon=True).start()

    webview.settings["ALLOW_DOWNLOADS"] = True

    # Create window
    window = webview.create_window(
        "Dashboard Ram",
        "http://127.0.0.1:8050",
        width=1200,
        height=800,
    )

    # Hook download handler
    webview.start(
        gui="edgechromium",  # on Windows use Edge backend for stability
        func=None,
        debug=False,
        http_server=False,
        private_mode=False,
        user_agent=None,
        localization={},
    )
