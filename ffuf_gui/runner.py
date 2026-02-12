import subprocess
import threading
import queue
import json
import shlex
import os
import signal
import time

class FfufRunner:
    def __init__(self):
        self.process = None
        self.output_queue = queue.Queue()
        self.running = False
        self.command_str = ""
        self._stop_event = threading.Event()

    def build_command(self, config):
        """Constructs the ffuf command list from configuration dictionary"""
        cmd = ["ffuf"]
        
        # URL needs special handling to ensure FUZZ keyword is present
        url = config.get("url", "")
        if "FUZZ" not in url and not config.get("recursion"):
             # Basic validation, though frontend should handle this too
             # If recursion is on, FUZZ might only be in -u if directory fuzzing
             pass 
        cmd.extend(["-u", url])

        # Wordlists
        # config['wordlists'] = [{"path": "...", "keyword": "FUZZ"}]
        for wl in config.get("wordlists", []):
            path = wl.get("path")
            keyword = wl.get("keyword", "FUZZ")
            if path:
                # Only add :KEYWORD if it's not the default FUZZ
                if keyword and keyword != "FUZZ":
                    cmd.extend(["-w", f"{path}:{keyword}"])
                else:
                    cmd.extend(["-w", path])

        # Method
        if config.get("method"):
            cmd.extend(["-X", config.get("method")])

        # Data (POST)
        if config.get("data"):
            cmd.extend(["-d", config.get("data")])
        
        # Headers
        # config['headers'] = ["Name: Value", ...]
        for header in config.get("headers", []):
            cmd.extend(["-H", header])

        # Matchers
        if config.get("mc"): cmd.extend(["-mc", config.get("mc")])
        if config.get("ms"): cmd.extend(["-ms", config.get("ms")])
        if config.get("mw"): cmd.extend(["-mw", config.get("mw")])
        if config.get("ml"): cmd.extend(["-ml", config.get("ml")])
        if config.get("mr"): cmd.extend(["-mr", config.get("mr")])
        
        # Filters
        if config.get("fc"): cmd.extend(["-fc", config.get("fc")])
        if config.get("fs"): cmd.extend(["-fs", config.get("fs")])
        if config.get("fw"): cmd.extend(["-fw", config.get("fw")])
        if config.get("fl"): cmd.extend(["-fl", config.get("fl")])
        if config.get("fr"): cmd.extend(["-fr", config.get("fr")])

        # General
        if config.get("threads"): cmd.extend(["-t", str(config.get("threads"))])
        if config.get("timeout"): cmd.extend(["-timeout", str(config.get("timeout"))])
        if config.get("recursion"): 
            cmd.append("-recursion")
            if config.get("recursion_depth"):
                cmd.extend(["-recursion-depth", str(config.get("recursion_depth"))])
        
        # Follow redirects
        if config.get("follow_redirects"):
            cmd.append("-r")
        
        # Ignore body
        if config.get("ignore_body"):
            cmd.append("-ignore-body")
        
        # Output options
        if config.get("output_file"):
            cmd.extend(["-o", config.get("output_file")])
        
        if config.get("output_format"):
            cmd.extend(["-of", config.get("output_format")])
        
        if config.get("silent"):
            cmd.append("-s")
        
        if config.get("verbose"):
            cmd.append("-v")
        
        if config.get("colors"):
            cmd.append("-c")
        
        print(f"[DEBUG] FFUF Command: {cmd}")
        return cmd

    def start(self, config):
        if self.running:
            return False, "Process already running"

        try:
            # Validate wordlists exist
            for wl in config.get("wordlists", []):
                path = wl.get("path")
                if path and not os.path.isfile(path):
                    return False, f"Wordlist file not found: {path}"
            
            if not config.get("wordlists"):
                return False, "At least one wordlist is required"
            
            cmd = self.build_command(config)
            self.command_str = " ".join(shlex.quote(c) for c in cmd)
            
            # Reset state
            self.output_queue = queue.Queue()
            self._stop_event.clear()
            
            # Start process
            # On Windows, we need special handling for process groups
            import sys
            creationflags = 0
            if sys.platform == 'win32':
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=creationflags
            )
            self.running = True
            
            # Put initial message to queue
            self.output_queue.put({"type": "log", "data": f"Started: {self.command_str}"})
            
            # Start monitoring thread
            threading.Thread(target=self._monitor_output, daemon=True).start()
            
            return True, "Started"
        except FileNotFoundError:
            self.running = False
            return False, "ffuf not found. Make sure ffuf is installed and in your PATH."
        except Exception as e:
            self.running = False
            return False, str(e)

    def stop(self):
        if self.process and self.running:
            # Signal threads to stop reading
            self._stop_event.set()
            
            # Terminate the process
            try:
                import sys
                if sys.platform == 'win32':
                    # On Windows, use taskkill for reliable termination
                    try:
                        subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)], 
                                      capture_output=True, timeout=5)
                    except Exception:
                        self.process.kill()
                else:
                    self.process.terminate()
                    # Give it a moment to die gracefully
                    try:
                        self.process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait()
            except Exception as e:
                print(f"[DEBUG] Error stopping process: {e}")
            
            self.running = False
            self.output_queue.put({"type": "status", "data": "stopped"})
            return True
        return False

    def _monitor_output(self):
        # Read both stdout and stderr and send to the queue
        # Since we're not forcing JSON mode, we need to handle both formats
        
        def read_pipe(pipe, is_stderr):
            for line in iter(pipe.readline, ''):
                if self._stop_event.is_set():
                    break
                if line:
                    line_stripped = line.strip()
                    if not line_stripped:
                        continue
                    
                    # Try to parse as JSON (for when user enables json/ejson output)
                    try:
                        data = json.loads(line_stripped)
                        # If it's a result object (has 'url' and 'status'), send as result
                        if isinstance(data, dict) and 'url' in data and 'status' in data:
                            self.output_queue.put({"type": "result", "data": data})
                        else:
                            # Other JSON data, just log it
                            self.output_queue.put({"type": "log", "data": line_stripped})
                    except (json.JSONDecodeError, ValueError):
                        # Plain text output - send as log
                        self.output_queue.put({"type": "log", "data": line_stripped})
            pipe.close()

        t_out = threading.Thread(target=read_pipe, args=(self.process.stdout, False))
        t_err = threading.Thread(target=read_pipe, args=(self.process.stderr, True))
        
        t_out.start()
        t_err.start()
        
        self.process.wait()
        t_out.join()
        t_err.join()
        
        self.running = False
        self.output_queue.put({"type": "status", "data": "finished"})

# Global instance for single-user local usage
runner = FfufRunner()
