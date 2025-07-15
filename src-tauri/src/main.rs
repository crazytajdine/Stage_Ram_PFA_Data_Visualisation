use std::env;

use std::process::Command;
use sysinfo::{Signal, System};
use tauri::{path::BaseDirectory, Manager, WindowEvent};

static NAME_OF_EXE: &str = "server_dashboard";

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
                kill_processes_by_name();
            }

            _ => {}
        })
        .run(tauri::generate_context!())
        .expect("error running Tauri app");
}
#[cfg(not(debug_assertions))]

fn init_server() {
    kill_processes_by_name();
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

fn kill_processes_by_name() {
    let mut sys = System::new_all();
    sys.refresh_processes(sysinfo::ProcessesToUpdate::All, true);

    for (pid, process) in sys.processes() {
        if process.name() == NAME_OF_EXE {
            println!("Killing PID: {} ({})", pid, process.name().display());
            process.kill_with(Signal::Kill);
        }
    }
}
