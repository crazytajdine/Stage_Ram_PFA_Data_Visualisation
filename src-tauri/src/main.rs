use std::env;

use std::process::Command;
use tauri::{path::BaseDirectory, Manager, WindowEvent};

static NAME_OF_EXE: &str = "server_dashboard.app";

#[cfg(debug_assertions)]
fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error running Tauri app");
}
#[cfg(not(debug_assertions))]

fn main() {
    init_server();

    tauri::Builder::default()
        .on_window_event(|_, window_event| match window_event {
            WindowEvent::Destroyed { .. } => {
                kill_server(true);
            }

            _ => {}
        })
        .run(tauri::generate_context!())
        .expect("error running Tauri app");
}
#[cfg(not(debug_assertions))]

fn init_server() {
    kill_server(true);
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

fn kill_server(exist_ok: bool) {
    println!("destroying {}", NAME_OF_EXE);

    let command = Command::new("taskkill")
        .arg("/F")
        .arg("/IM")
        .arg(NAME_OF_EXE)
        .spawn();

    if exist_ok {
        match command {
            Ok(mut child) => {
                child.wait().expect("Failed to wait for child process");
                println!("Process killed successfully");
            }
            Err(err) => {
                println!("Error killing process: {}", err);
            }
        }
    }
}
