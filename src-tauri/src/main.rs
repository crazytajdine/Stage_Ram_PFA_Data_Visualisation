use std::process::{Child, Command};
use tauri::{ WindowEvent};

static PATH: &str = r"C:/Users/tajdi/Documents/tauri-app/dist/server_dashboard.exe";

fn main() {


     init_server();

        
        
        tauri::Builder::default().on_window_event(|_,window_event|  {
            match window_event {
                
                WindowEvent::Destroyed {..}=>{
                kill_server();
            }
            
            _ => {}
        }
    })
    .run(tauri::generate_context!())
        .expect("error running Tauri app");

}

fn init_server(){
    kill_server();
    start_server();
}

fn start_server() {
    let _: Child = Command::new(PATH)
         .spawn()
         .expect("Failed to start backend");
}

fn kill_server() {
    let name_out_exe: &str = PATH.split('/').last().unwrap_or("main.exe");
    println!("destroying {}",name_out_exe);
                
    let _ = Command::new("taskkill")
        .arg("/F")
        .arg("/IM")
        .arg(name_out_exe)
        .spawn()
        .expect("Failed to kill backend");
}
