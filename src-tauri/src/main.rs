use std::path::Path;
use std::process::{Command, Child};
use std::sync::Mutex;

use once_cell::sync::OnceCell;
use ureq;

static BACKEND_CHILD: OnceCell<Mutex<Child>> = OnceCell::new();
static PATH: &str = r"C:/Users/tajdi/Documents/tauri-app/dist/main.exe";
static URL: &str = "http://127.0.0.1:8050";

fn is_backend_running() -> bool {
    ureq::get(URL).call().ok().is_some()
}

fn main() {
    #[cfg(not(debug_assertions))]
    {
        if !is_backend_running() {
            // Spawn backend if URL is not responding
            let child = Command::new(PATH)
                .spawn()
                .expect("Failed to start backend");

            BACKEND_CHILD.set(Mutex::new(child)).ok();
        }
    }

    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error running Tauri app");
}
