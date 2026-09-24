#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;
use tauri_plugin_shell::ShellExt;
use std::sync::Mutex;

struct AppState {
    backend_port: Mutex<Option<u16>>,
}

#[tauri::command]
fn get_backend_port(state: tauri::State<AppState>) -> Option<u16> {
    state.backend_port.lock().unwrap().clone()
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(AppState {
            backend_port: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![get_backend_port])
        .setup(|app| {
            let app_handle = app.handle().clone();

            // Spawn Python sidecar
            let sidecar = app_handle
                .shell()
                .sidecar("paperquant-server")
                .expect("Failed to create sidecar command");

            let (mut rx, _child) = sidecar
                .spawn()
                .expect("Failed to spawn Python sidecar");

            // Listen for stdout to capture port
            let handle_clone = app_handle.clone();
            tauri::async_runtime::spawn(async move {
                use tauri_plugin_shell::process::CommandEvent;

                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            let line_str = String::from_utf8_lossy(&line);

                            // Parse port from "PAPERQUANT_PORT=XXXXX"
                            if let Some(port_str) = line_str.strip_prefix("PAPERQUANT_PORT=") {
                                if let Ok(port) = port_str.trim().parse::<u16>() {
                                    // Store port in app state
                                    let state = handle_clone.state::<AppState>();
                                    *state.backend_port.lock().unwrap() = Some(port);

                                    // Inject port into all windows
                                    if let Some(window) = handle_clone.get_webview_window("main") {
                                        let js = format!(
                                            "window.__PAPERQUANT_PORT__ = {};",
                                            port
                                        );
                                        let _ = window.eval(&js);
                                    }

                                    println!("Backend started on port {}", port);
                                }
                            }
                        }
                        CommandEvent::Stderr(line) => {
                            eprintln!("Backend stderr: {}", String::from_utf8_lossy(&line));
                        }
                        CommandEvent::Terminated(status) => {
                            eprintln!("Backend process terminated with status: {:?}", status);
                        }
                        _ => {}
                    }
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("Error running PaperQuant");
}
