import socket
import subprocess
import tempfile
import os
import shutil

def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def launch_chromium(headless=False, suppress_output=True):
    chromium_path = "chromium"
    user_data_dir = tempfile.mkdtemp(prefix="chrome-profile-")
    cdp_port = _find_free_port()

    # Launch Chromium with the provided parameters
    args = [
        chromium_path,
        f"--remote-debugging-port={cdp_port}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--remote-allow-origins=*",
        "--no-default-browser-check",
        "--log-level=3",  # Minimal logging, errors only
        "--silent-debugger-extension-api",  # Reduce extension API logging
    ]
    if headless:
        args.append("--headless=new")

    # Handle output redirection
    if suppress_output:
        # Redirect both stdout and stderr to /dev/null (or NUL on Windows)
        devnull = open(os.devnull, 'w')
        process = subprocess.Popen(args, stdout=devnull, stderr=devnull)
    else:
        process = subprocess.Popen(args)
        
    print(f"Chromium launched on port {cdp_port}.")

    def kill():
        os.system(f"pkill -f 'remote-debugging-port={cdp_port}'")
        shutil.rmtree(user_data_dir, ignore_errors=True)
        print("Chromium killed and user data dir cleaned up.")

    return kill, cdp_port


