#!/bin/bash
echo "Starting Stock Analyzer Desktop..."

# Ensure dependencies are installed
if [ ! -d "desktop/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd desktop
    npm install
    cd ..
fi

# Run Tauri App
cd desktop
npm run tauri dev
