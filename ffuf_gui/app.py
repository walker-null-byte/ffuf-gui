import os
import sys
import queue
import json
import time
import socket
from flask import Flask, render_template, request, Response, jsonify
from ffuf_gui.runner import runner

app = Flask(__name__)
def main():
    port = 5000
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                break
        port += 1
    app.run(debug=True, port=port, threaded=True)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/run', methods=['POST'])
def run_ffuf():
    config = request.json
    if not config:
        return jsonify({"error": "No configuration provided"}), 400
    
    # Basic validation before starting
    if not config.get('url'):
        return jsonify({"error": "URL is required"}), 400
    
    success, message = runner.start(config)
    if success:
        return jsonify({"status": "started", "message": message})
    else:
        return jsonify({"status": "error", "message": message}), 500

@app.route('/api/stop', methods=['POST'])
def stop_ffuf():
    if runner.stop():
        return jsonify({"status": "stopped"})
    return jsonify({"status": "not_running"}), 400

@app.route('/api/stream')
def stream_output():
    def generate():
        while True:
            try:
                # Non-blocking get
                item = runner.output_queue.get(timeout=1)
                yield f"data: {json.dumps(item)}\n\n"
            except queue.Empty:
                if not runner.running and runner.output_queue.empty():
                    # Process finished and queue empty
                    yield f"data: {json.dumps({'type': 'status', 'data': 'finished'})}\n\n"
                    break
                # Keep alive
                yield ": keepalive\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
    
    return Response(generate(), mimetype="text/event-stream")

@app.route('/api/browse', methods=['POST'])
def browse_file():
    """Open a native file dialog and return the selected file path"""
    import threading
    result = {"path": None}
    
    def open_dialog():
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            # Create a hidden root window
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)  # Bring dialog to front
            
            # Open file dialog
            file_path = filedialog.askopenfilename(
                title="Select Wordlist File",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("Wordlist files", "*.lst"),
                    ("All files", "*.*")
                ]
            )
            
            root.destroy()
            
            if file_path:
                result["path"] = file_path
        except Exception as e:
            result["error"] = str(e)
    
    # Run dialog in a separate thread to avoid blocking
    dialog_thread = threading.Thread(target=open_dialog)
    dialog_thread.start()
    dialog_thread.join(timeout=60)  # Wait up to 60 seconds for user to select file
    
    if result.get("path"):
        return jsonify({"success": True, "path": result["path"]})
    elif result.get("error"):
        return jsonify({"success": False, "error": result["error"]})
    else:
        return jsonify({"success": False, "error": "No file selected"})

@app.route('/api/browse_save', methods=['POST'])
def browse_save_file():
    """Open a native save file dialog and return the selected file path"""
    import threading
    result = {"path": None}
    
    def open_dialog():
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            # Create a hidden root window
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)  # Bring dialog to front
            
            # Open save file dialog
            file_path = filedialog.asksaveasfilename(
                title="Save Output File",
                defaultextension=".json",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("HTML files", "*.html"),
                    ("CSV files", "*.csv"),
                    ("Markdown files", "*.md"),
                    ("All files", "*.*")
                ]
            )
            
            root.destroy()
            
            if file_path:
                result["path"] = file_path
        except Exception as e:
            result["error"] = str(e)
    
    # Run dialog in a separate thread to avoid blocking
    dialog_thread = threading.Thread(target=open_dialog)
    dialog_thread.start()
    dialog_thread.join(timeout=60)
    
    if result.get("path"):
        return jsonify({"success": True, "path": result["path"]})
    elif result.get("error"):
        return jsonify({"success": False, "error": result["error"]})
    else:
        return jsonify({"success": False, "error": "No file selected"})

@app.route('/api/validate', methods=['POST'])
def validate_inputs():
    data = request.json
    path = data.get('path')
    if path:
        if os.path.exists(path) and os.path.isfile(path):
             return jsonify({"valid": True})
        return jsonify({"valid": False, "error": "File not found"})
    return jsonify({"valid": True})

if __name__ == "__main__":
    main()