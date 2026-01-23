// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let builder = tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init()) // Init shell plugin
        .invoke_handler(tauri::generate_handler![greet]);

    let builder = builder.setup(|app| {
        use tauri::Manager;
        use std::process::Command;
        
        let handle = app.handle().clone();
        
        tauri::async_runtime::spawn(async move {
            let resource_path = handle
                .path()
                .resolve("python_backend", tauri::path::BaseDirectory::Resource)
                .expect("failed to resolve resource");
            
            let exe_path = if cfg!(target_os = "windows") {
                resource_path.join("stock_server.exe")
            } else {
                resource_path.join("stock_server")
            };
            
            println!("Launching backend from: {:?}", exe_path);

            let mut command = Command::new(exe_path);
            
             // Spawn the process
            let child = command.spawn();
            
            match child {
                Ok(mut c) => {
                     println!("Backend started successfully");
                     // Wait for it? No, it should run in background.
                     // But we should probably keep track of it to kill it?
                     // For now, let's just let it run.
                     // On Windows, closing parent might not close child if not handled.
                     // But we can rely on our zombie killer in python.
                }
                Err(e) => {
                    eprintln!("Failed to start backend: {}", e);
                }
            }
        });

        Ok(())
    });

    builder
        .build(tauri::generate_context!())
        .expect("error while running tauri application")
        .run(|_app, _event| {});
}

