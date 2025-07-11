use std::env;

use std::process::Command;
use tauri::{path::BaseDirectory, Manager, WindowEvent};

static NAME_OF_EXE: &str = "server_dashboard.exe";

#[cfg(debug_assertions)]
fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error running Tauri app");
}

#[cfg(not(debug_assertions))]
fn main() {
    let path_to_server = env::current_dir().unwrap().join(NAME_OF_EXE);

    println!("Current directory: {}", path_to_server.display());

    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error running Tauri app");

    init_server();

    tauri::Builder::default()
        .on_window_event(|_, window_event| match window_event {
            WindowEvent::Destroyed { .. } => {
                kill_server();
            }

            _ => {}
        })
        .run(tauri::generate_context!())
        .expect("error running Tauri app");
}

#[cfg(not(debug_assertions))]
fn init_server() {
    kill_server();
    start_server();
}

#[cfg(not(debug_assertions))]
fn start_server() {
    let path_to_server = env::current_dir().unwrap().join(NAME_OF_EXE);

    println!("Openning: {}", path_to_server.display());

    let _ = Command::new(path_to_server)
        .spawn()
        .expect("Failed to start backend");
}

#[cfg(not(debug_assertions))]
fn kill_server() {
    println!("destroying {}", NAME_OF_EXE);

    let _ = Command::new("taskkill")
        .arg("/F")
        .arg("/IM")
        .arg(NAME_OF_EXE)
        .spawn()
        .expect("Failed to kill backend");
}
