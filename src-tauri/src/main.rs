// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    #[cfg(not(debug_assertions))]
    {
        // This block runs ONLY in production build (release mode)
        Command::new("dist/app.exe")  // or "dist/app" on Linux/macOS
            .spawn()
            .expect("failed to start Dash backend");
    }
    


    tauri_app_lib::run()
}
