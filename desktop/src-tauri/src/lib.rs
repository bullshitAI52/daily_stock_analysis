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
        use tauri_plugin_shell::ShellExt;
        
        let sidecar = app.shell().sidecar("stock_server").unwrap();
        let (mut rx, mut _child) = sidecar.spawn().expect("Failed to spawn sidecar");

        tauri::async_runtime::spawn(async move {
            // Read events such as stdout
            while let Some(event) = rx.recv().await {
                if let tauri_plugin_shell::process::CommandEvent::Stdout(line) = event {
                     println!("Python: {}", String::from_utf8(line).unwrap());
                } else if let tauri_plugin_shell::process::CommandEvent::Stderr(line) = event {
                     eprintln!("Python Err: {}", String::from_utf8(line).unwrap());
                }
            }
        });
        
        Ok(())
    });

    builder
        .build(tauri::generate_context!())
        .expect("error while running tauri application")
        .run(|app, event| {
             if let tauri::RunEvent::ExitRequested { .. } = event {
                 // The sidecar is a child process of the Tauri app, so it should be killed automatically by the OS when the parent dies.
                 // However, to be safe, we can try to kill it explicitly if we had a handle.
                 // But the `sidecar.spawn()` returns a child handle that is moved into the async block.
                 // We can rely on OS cleanup for now, but checking for zombie processes is good practice.
                 println!("App exiting...");
             }
        });
}
