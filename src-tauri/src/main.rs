use std::process::{Child, Command, Stdio};
use tauri::{Emitter, Listener, Manager};

static PATH: &str = r"C:/Users/tajdi/Documents/tauri-app/dist/server_dashboard.exe";

fn main() {

    // let _: Child = Command::new(PATH)
    //     .stdout(Stdio::piped())
    //     .spawn()
    //     .expect("Failed to start backend");

    let name_out_exe: &str = PATH.split('/').last().unwrap_or("main.exe");

    tauri::Builder::default()
        .setup(move |app| {
            let handle = app.handle();

            handle.listen("open-notepad", move |_event| {
                println!("Received event to open Notepad!");
                let _ = Command::new("notepad.exe").spawn();
            });
            if let Some(main_window) = app.get_webview_window("main") {
                main_window
                    .emit_str("event-name", "Hello from Rust!".to_string())
                    .unwrap();
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error running Tauri app");

    // let _ = Command::new("taskkill")
    //     .stdout(Stdio::piped())
    //     .arg("/F")
    //     .arg("/IM")
    //     .arg(name_out_exe)
    //     .spawn()
    //     .expect("Failed to kill backend");
}
