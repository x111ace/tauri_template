import os, json, time, shutil, argparse, subprocess, sys, platform
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(SCRIPT_DIR, "config")
LOG_FILE = os.path.join(CONFIG_DIR, "build.log")

# Platform detection for cross-platform compatibility
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

# Colorama for colored terminal output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    RRR = Style.RESET_ALL
    BRT = Style.BRIGHT
    DIM = Style.DIM
    RED = Fore.RED
    GRN = Fore.GREEN
    YLW = Fore.YELLOW
    BLU = Fore.BLUE
    MGN = Fore.MAGENTA
    CYN = Fore.CYAN
except ImportError:
    # Fallback for systems without colorama
    RRR = BRT = DIM = RED = GRN = YLW = BLU = MGN = CYN = ""

# Files and folders to exclude during cleaning and tree views
JSPROJECT_EXCLUDE = {".svelte-kit", "dist", "node_modules", "package-lock.json", "build"}
PYPROJECT_EXCLUDE = {"__pycache__", "venv"}
RSPROJECT_EXCLUDE = {"target", "Cargo.lock"}
EXCLUDE_ALL = {"build.log", ".vscode", "dox"} | PYPROJECT_EXCLUDE | JSPROJECT_EXCLUDE | RSPROJECT_EXCLUDE

# Exclusions for the tree view should be more comprehensive
TREE_EXCLUDE = EXCLUDE_ALL | {".git"}

# Language extensions for project tree statistics
PROG_LANG_EXTS = {
    ".py": "Python", 
    ".ipynb": "Jupyter Notebook",
    ".rs": "Rust", 
    ".js": "JavaScript", 
    ".ts": "TypeScript", 
    ".c": "C",
    ".cpp": "C++", 
    ".h": "C/C++ Header", 
    ".java": "Java", 
    ".html": "HTML",
    ".css": "CSS", 
    ".sh": "Shell Script",
    ".svelte": "Svelte",
}

# --- Configuration Reading Functions ---

def read_tauri_config(root_dir: str):
    """Reads and parses the tauri.conf.json file to extract dynamic configuration."""
    config_path = os.path.join(root_dir, "tauri.conf.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        product_name = config.get("package", {}).get("productName", "tauri-app")
        return {
            "product_name": product_name,
            "app_name": product_name.lower().replace(" ", "-"),
            "identifier": config.get("tauri", {}).get("bundle", {}).get("identifier", "com.example.app")
        }
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"{YLW}Warning: Could not read tauri.conf.json ({e}). Using defaults.{RRR}", flush=True)
        return {
            "product_name": "Tauri App",
            "app_name": "tauri-app", 
            "identifier": "com.example.app"
        }

def get_platform_commands():
    """Returns platform-specific commands for npm and process management."""
    if IS_WINDOWS:
        return {
            "npm": "npm.cmd",
            "kill_cmd": "taskkill",
            "kill_args": ["/F", "/T", "/IM"], # /T terminates child processes
            "executable_ext": ".exe"
        }
    else:  # macOS and Linux
        return {
            "npm": "npm",
            "kill_cmd": "pkill", 
            "kill_args": ["-f"],
            "executable_ext": ""
        }

# --- Core Functions ---

def project_tree(root_dir: str, output: bool = False) -> str:
    """Generates and optionally prints a complete file tree with statistics."""
    tree_lines = []
    stats = {"folders": 0, "files": {"total": 0, "by_type": {}}}

    def count_lines(path: str) -> int:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except (IOError, OSError):
            return 0

    def process_directory(dir_path: str, prefix: str = ""):
        """Recursively process a directory to build the tree."""
        try:
            entries = sorted(os.listdir(dir_path), key=lambda e: (os.path.isfile(os.path.join(dir_path, e)), e.lower()))
        except OSError:
            return
        
        entries = [e for e in entries if e not in TREE_EXCLUDE]
        
        for i, entry in enumerate(entries):
            path = os.path.join(dir_path, entry)
            connector = "└── " if i == len(entries) - 1 else "├── "
            
            if os.path.isdir(path):
                stats["folders"] += 1
                tree_lines.append(f"{prefix}{connector}{BRT}{BLU}{entry}{RRR}/")
                extension = "    " if i == len(entries) - 1 else "│   "
                process_directory(path, prefix + extension)
            else:
                stats["files"]["total"] += 1
                ext = os.path.splitext(entry)[1]
                lang = PROG_LANG_EXTS.get(ext)
                
                if lang:
                    lines = count_lines(path)
                    lang_stats = stats["files"]["by_type"].setdefault(lang, {'files': 0, 'lines': 0})
                    lang_stats['files'] += 1
                    lang_stats['lines'] += lines
                    tree_lines.append(f"{prefix}{connector}{entry} :: {GRN}{lines}{RRR} lines")
                else:
                    tree_lines.append(f"{prefix}{connector}{entry}")

    abs_root = os.path.abspath(root_dir)
    root_label = f"{BLU}{os.path.basename(abs_root.rstrip(os.sep))}{RRR}/"
    tree_lines.append(root_label)
    process_directory(abs_root)
    
    file_tree_str = "\n".join(tree_lines)
    if output:
        print(json.dumps(stats, indent=4), flush=True)
        print(file_tree_str, flush=True)
    
    return file_tree_str

def confirm_action(message: str, default: bool = False) -> bool:
    """Ask user for confirmation before performing potentially destructive actions."""
    prompt = f"{YLW}{message}{RRR} "
    if default:
        prompt += f"[{GRN}Y{RRR}/n] "
    else:
        prompt += f"[y/{RED}N{RRR}] "
    
    try:
        response = input(prompt).strip().lower()
        if not response:
            return default
        return response in ['y', 'yes', 'true', '1']
    except (KeyboardInterrupt, EOFError):
        print(f"\n{YLW}Operation cancelled.{RRR}", flush=True)
        return False

def clean_project(root_dir: str, output: bool = False, force: bool = False):
    """Walks the root directory and removes files/folders with an optimized strategy."""
    if output:
        print(f"{CYN}Preparing to clean project...{RRR}", flush=True)
    
    stop_dev_servers(root_dir, output)
    
    # Efficiently find all items to be cleaned, without descending into excluded directories.
    paths_to_remove = []
    for root, dirs, files in os.walk(root_dir, topdown=True):
        # Prune the directories list in-place to prevent os.walk from descending into them.
        # We iterate over a copy of dirs `list(dirs)` because we modify it.
        for d in list(dirs):
            if d in EXCLUDE_ALL:
                full_path = os.path.join(root, d)
                paths_to_remove.append(full_path)
                dirs.remove(d)  # This is the key optimization

        # Add any matching files from the current directory.
        for f in files:
            if f in EXCLUDE_ALL:
                paths_to_remove.append(os.path.join(root, f))

    if not paths_to_remove:
        if output:
            print(f"{GRN}Project is already clean. No items to remove.{RRR}", flush=True)
        return

    # Separate paths into files and directories
    files_to_delete = []
    dirs_to_delete = []
    for p in paths_to_remove:
        if os.path.isfile(p):
            try:
                files_to_delete.append({'path': p, 'size': os.path.getsize(p)})
            except OSError:
                continue 
        elif os.path.isdir(p):
            dirs_to_delete.append({'path': p})

    # As requested, sort files by size (smallest to largest)
    files_to_delete.sort(key=lambda f: f['size'])
    
    # The final list for deletion: files first, then directories.
    items_to_clean = [f['path'] for f in files_to_delete] + [d['path'] for d in dirs_to_delete]

    if output and not force:
        print(f"{YLW}The following items will be removed (files first, then folders):{RRR}", flush=True)
        for item in items_to_clean[:10]:  # Show first 10 items
            if os.path.exists(item):
                print(f"  - {item}", flush=True)
        if len(items_to_clean) > 10:
            print(f"  ... and {len(items_to_clean) - 10} more items", flush=True)
        
        if not confirm_action("Are you sure you want to delete these items?", default=False):
            print(f"{YLW}Clean operation cancelled.{RRR}", flush=True)
            return

    # Separate the log file from other items to avoid a file lock conflict.
    log_file_path_to_delete = None
    items_for_main_loop = []
    for item in items_to_clean:
        try:
            if os.path.exists(item) and os.path.samefile(item, LOG_FILE):
                log_file_path_to_delete = item
            else:
                items_for_main_loop.append(item)
        except FileNotFoundError:
            continue
            
    with open(LOG_FILE, 'a', encoding='utf-8') as log:
        log.write(f"\n--- Starting Clean Operation at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        for item_path in items_for_main_loop: # Note: iterating over the filtered list
            if not os.path.exists(item_path):
                continue
            
            log.write(f"Attempting to remove: {item_path}\n")
            log.flush()
            
            if output:
                print(f"{DIM}Attempting to remove: {item_path}...{RRR}", end="", flush=True)

            for attempt in range(3):
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    elif os.path.isfile(item_path):
                        os.remove(item_path)
                    
                    log.write(f"Successfully removed: {item_path}\n")
                    log.flush()

                    if output:
                        print(f"\r{GRN}Successfully removed: {item_path.ljust(80)}{RRR}", flush=True)
                    break
                except OSError as e:
                    log.write(f"Failed attempt to remove {item_path}: {e}\n")
                    log.flush()
                    if attempt < 2:
                        if output:
                            print(f"\r{YLW}Could not remove {item_path}, retrying... ({e}){RRR}", flush=True)
                        time.sleep(2)
                    else:
                        if output:
                            print(f"\r{RED}Failed to remove {item_path}: {e}{RRR}", flush=True)

    # Now that the log file is closed, we can safely delete it.
    if log_file_path_to_delete:
        try:
            if output:
                print(f"{DIM}Attempting to remove log file: {log_file_path_to_delete}...{RRR}", end="", flush=True)
            os.remove(log_file_path_to_delete)
            if output:
                print(f"\r{GRN}Successfully removed log file: {log_file_path_to_delete.ljust(80)}{RRR}", flush=True)
        except OSError as e:
            if output:
                print(f"\r{RED}Failed to remove log file {log_file_path_to_delete}: {e}{RRR}", flush=True)


# --- Helper Functions ---

def stop_dev_servers(root_dir: str, output: bool = False):
    """Stops running development servers using cross-platform commands."""
    if output:
        print(f"{CYN}Stopping any running development servers...{RRR}", flush=True)

    config = read_tauri_config(root_dir)
    commands = get_platform_commands()
    
    # Cross-platform process cleanup
    app_name = config["app_name"]
    executable_ext = commands["executable_ext"]
    
    lingering_processes = [
        f"cargo{executable_ext}",
        f"vite{executable_ext}",
        f"node{executable_ext}",
        f"{app_name}{executable_ext}"
    ]
    
    for proc_name in lingering_processes:
        if output:
            print(f"{DIM}Attempting to stop process: {proc_name}...{RRR}", end="", flush=True)
        try:
            if IS_WINDOWS:
                result = subprocess.run(
                    [commands["kill_cmd"]] + commands["kill_args"] + [proc_name], 
                    check=False, 
                    capture_output=True,
                    timeout=5 # Reduced timeout
                )
            else:
                # For Unix-like systems, use pkill with pattern matching
                result = subprocess.run(
                    [commands["kill_cmd"]] + commands["kill_args"] + [proc_name.replace(executable_ext, "")], 
                    check=False, 
                    capture_output=True,
                    timeout=5 # Reduced timeout
                )
            
            # On Windows, error code 128 means "not found", which is a success for us.
            # On Linux/macOS, error code 1 means "not found".
            success_codes = [0, 128] if IS_WINDOWS else [0, 1]

            if output:
                if result.returncode in success_codes:
                    print(f"\r{GRN}Stopped (or wasn't running): {proc_name.ljust(60)}{RRR}", flush=True)
                else:
                    print(f"\r{YLW}Could not stop {proc_name}. Return code: {result.returncode}{''.ljust(20)}{RRR}", flush=True)

        except FileNotFoundError:
            if output:
                print(f"\r{YLW}Process management tool '{commands['kill_cmd']}' not found.{''.ljust(30)}{RRR}", flush=True)
            break 
        except subprocess.TimeoutExpired:
            if output:
                print(f"\r{RED}Timeout trying to stop {proc_name}. It might be a zombie process.{''.ljust(20)}{RRR}", flush=True)
    
    if output:
        print(f"{CYN}Waiting for processes to terminate fully...{RRR}", flush=True)
    time.sleep(3)  # A brief pause to allow OS to release file handles.

def start_dev_servers(root_dir: str, output: bool = False):
    """Launches the development server and keeps the script running."""
    if output:
        print(f"\n{BRT}{CYN}--- Starting Development Environment ---{RRR}")
        print(f"{YLW}The server is now running and watching for file changes.{RRR}")
        print(f"{YLW}Press Ctrl+C in this terminal to stop the server.{RRR}")
    
    commands = get_platform_commands()
    _run_command([commands["npm"], "run", "dev"], root_dir, LOG_FILE, show_output=output)
    
    if output:
        print(f"\n{GRN}Development server process ended.{RRR}")

def _run_command(command: list[str], cwd: str, log_file_path: str, show_output: bool = True):
    """A centralized helper to run subprocess commands with real-time logging to console and file."""
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"\n--- Running Command: {' '.join(command)} ---\n")
            if show_output:
                print(f"{DIM}--- Running Command: {' '.join(command)} ---{RRR}")

            while True:
                line = process.stdout.readline()
                if not line:
                    break
                if show_output:
                    print(line, end='')
                log_file.write(line)
                log_file.flush()
        
        return_code = process.wait()
        
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)

    except FileNotFoundError:
        print(f"{RED}Error: Command '{command[0]}' not found. Is it in your PATH?{RRR}")
        raise
    except subprocess.CalledProcessError as e:
        print(f"\n{RED}Error running command: {' '.join(command)}. Return code: {e.returncode}.{RRR}")
        print(f"{YLW}Check '{log_file_path}' for the complete log.{RRR}")
        raise e

# --- Project Lifecycle Functions ---

def prepare_build_assets(root_dir: str, output: bool = False):
    """Ensures required icon assets are in place before building."""
    if output:
        print(f"{CYN}Preparing build assets...{RRR}", flush=True)
    
    icons_dir = os.path.join(root_dir, "icons")
    source_icons_dir = os.path.join(icons_dir, "favicon_io")
    
    # Define required assets and their sources
    required_assets = {
        "icon.png": "android-chrome-512x512.png",
        "favicon.ico": "favicon.ico"
    }

    for dest, src in required_assets.items():
        dest_path = os.path.join(icons_dir, dest)
        src_path = os.path.join(source_icons_dir, src)
        
        if not os.path.exists(dest_path):
            if os.path.exists(src_path):
                if output:
                    print(f"{DIM}Asset '{dest}' missing. Copying from source...{RRR}", flush=True)
                shutil.copy(src_path, dest_path)
            else:
                if output:
                    print(f"{YLW}Warning: Source asset '{src}' not found in '{source_icons_dir}'. Cannot prepare '{dest}'.{RRR}", flush=True)

def install_dependencies(root_dir: str, output: bool = False):
    """Installs npm dependencies if the node_modules directory is not present."""
    node_modules_path = os.path.join(root_dir, 'node_modules')
    if os.path.exists(node_modules_path):
        if output:
            print(f"{GRN}Dependencies already exist. Skipping 'npm install'.{RRR}", flush=True)
        return

    if output:
        print(f"{CYN}Dependencies not found. Installing... (this may take a moment){RRR}", flush=True)
    
    commands = get_platform_commands()
    # Make this step verbose so the user sees progress instead of a 'frozen' screen.
    _run_command([commands["npm"], "install"], root_dir, LOG_FILE, show_output=True)
    if output:
        print(f"{GRN}Dependencies installed successfully.{RRR}", flush=True)

def build_project(root_dir: str, output: bool = False):
    """Builds the project for production."""
    if output:
        print(f"{CYN}Building project for production...{RRR}", flush=True)
    # Ensure dependencies are installed before building.
    install_dependencies(root_dir, output)
    
    # Ensure required assets like icons are in place.
    prepare_build_assets(root_dir, output)

    # Always clear the log file for a clean record
    with open(LOG_FILE, 'w') as f:
        f.write(f"--- New Build Initiated at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    
    if output:
        print(f"\n{BRT}{YLW}The next step involves compiling the Rust backend. This can take several minutes{RRR}", flush=True)
        print(f"{YLW}without providing detailed output. Please be patient, the script will load the build output.{RRR}", flush=True)

    commands = get_platform_commands()        
    _run_command([commands["npm"], "run", "build"], root_dir, LOG_FILE, show_output=output)

    # --- Verification Step ---
    config = read_tauri_config(root_dir)
    app_name = config["app_name"]
    executable_ext = commands["executable_ext"]
    executable_path = os.path.join(root_dir, 'target', 'release', f'{app_name}{executable_ext}')
    
    if not os.path.exists(executable_path):
        if output:
            print(f"{YLW}WARNING: Production executable not found at expected path.{RRR}", flush=True)
            print(f"{YLW}Path checked: {executable_path}{RRR}", flush=True)
            print(f"{YLW}This might be normal if you built for a different target.{RRR}", flush=True)

    if output:
        print(f"{GRN}Production build completed successfully.{RRR}", flush=True)

def init_project(root_dir, output=False):
    """
    Initializes the project fully by ensuring servers are stopped,
    installing dependencies, running an initial build, and then 
    starting the live development servers.
    """
    if output:
        print(f"{BRT}{MGN}--- Initiating Full Project Setup ---{RRR}", flush=True)
    
    # 0. Stop any lingering dev servers to ensure a clean start.
    stop_dev_servers(root_dir, output)
    
    # 1. Install dependencies if needed.
    install_dependencies(root_dir, output)
    
    # 2. Run a one-time build to generate initial dist files.
    build_project(root_dir, output)
    
    # 3. Start the live development servers for hot reloading.
    start_dev_servers(root_dir, output)

    if output:
        print(f"{BRT}{GRN}--- Project setup complete. Happy coding! ---{RRR}", flush=True)

# --- History Logging Functions ---

def log_command_history(root_dir: str, command: str):
    """Logs the executed script command to JSON and MDC files for history and AI context."""
    
    # Define paths for the log files
    cursor_rules_dir = os.path.join(root_dir, ".cursor", "rules")
    config_dir = os.path.join(root_dir, "config")
    
    mdc_log_path = os.path.join(cursor_rules_dir, "dev-history.mdc")
    json_log_path = os.path.join(config_dir, "dev-history.json")

    # Ensure target directories exist
    os.makedirs(cursor_rules_dir, exist_ok=True)
    os.makedirs(config_dir, exist_ok=True)

    # Create the log entry
    log_entry = {
        "command": command,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # --- Update JSON Log ---
    history = []
    if os.path.exists(json_log_path):
        try:
            with open(json_log_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupt or unreadable, start fresh
            history = []
    
    history.append(log_entry)
    with open(json_log_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4)

    # --- Update MDC Log ---
    mdc_header = "---\nalwaysApply: true\n---\n\n"
    if not os.path.exists(mdc_log_path):
        with open(mdc_log_path, 'w', encoding='utf-8') as f:
            f.write(mdc_header)

    with open(mdc_log_path, 'a', encoding='utf-8') as f:
        f.write(f"```json\n{json.dumps(log_entry, indent=4)}\n```\n\n")


# --- Main Execution Block ---

def main():
    """Parses command-line arguments and executes the corresponding function."""
    parser = argparse.ArgumentParser(
        description="A cross-platform utility script for managing your Svelte/Tauri project.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-t", "--tree", 
        action="store_true", help="Display the project's file tree with statistics."
    )
    parser.add_argument("-c", "--clean", 
        action="store_true", help="Clean all build artifacts and dependencies."
    )
    parser.add_argument("--force", 
        action="store_true", help="Force operations without confirmation prompts."
    )
    parser.add_argument("-x", "--stop", 
        action="store_true", help="Stop any running development servers."
    )
    parser.add_argument("-f", "--deps", 
        action="store_true", help="Clean and reinstall all npm dependencies."
    )
    parser.add_argument("-b", "--build", 
        action="store_true", help="Build the project for production."
    )
    parser.add_argument("-d", "--dev", 
        action="store_true", help="Start the live development server."
    )
    parser.add_argument("-i", "--init", 
        action="store_true", help="Initialize the project fully (clean, deps, build, dev)."
    )
    
    args = parser.parse_args()

    # Log the command that was run
    if len(sys.argv) > 1:
        command_run = "python " + " ".join(sys.argv)
        log_command_history(SCRIPT_DIR, command_run)

    if args.tree:
        project_tree(SCRIPT_DIR, output=True)
    elif args.clean:
        clean_project(SCRIPT_DIR, output=True, force=args.force)
    elif args.stop:
        stop_dev_servers(SCRIPT_DIR, output=True)
    elif args.deps:
        print(f"{BRT}{CYN}--- Force Reinstalling Dependencies ---{RRR}", flush=True)
        clean_project(SCRIPT_DIR, output=True, force=args.force)
        install_dependencies(SCRIPT_DIR, output=True)
    elif args.build:
        build_project(SCRIPT_DIR, output=True)
    elif args.dev:
        start_dev_servers(SCRIPT_DIR, output=True)
    elif args.init:
        try:
            init_project(SCRIPT_DIR, output=True)
        except KeyboardInterrupt:
            print(f"\n{YLW}KeyboardInterrupt detected. Stopping development servers...{RRR}", flush=True)
            stop_dev_servers(SCRIPT_DIR, output=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"\n{RED}Project initialization failed: {e}{RRR}", flush=True)
    else:
        parser.print_help()

if __name__ == "__main__":
    # # Clean the project
    # python __mgr__.py -c

    # # Create a tree to see it
    # python __mgr__.py -t

    # # Build alone
    # python __mgr__.py -b

    # # Run what was built
    # python __mgr__.py -d

    # # Clean it again
    # python __mgr__.py -c
    
    # # Run with the magic all-in one starter
    # python __mgr__.py -i

    ### ### ### ### ### ### ### ### ###

    # To improve the script, we can make a dev enviornment 'tracker' to log the run command history.
    # We can write to a rules file, and a JSON, to ensure the AI can understand the context of the dev environment.
    # If any path or file doesn't exist, we'll create it. We'll target the `.cursor/` folder and the `config/` folder.
        # We will create a rules file and a JSON log named `dev-history` (`.mdc` & `.json`).
        # The rules file MUST contain the following:
            # ---
            # alwaysApply: true
            # ---
        # The JSON log MUST contain the following:
            # {
            #     "command": "python __mgr__.py -c",
            #     "timestamp": "2025-07-27 12:00:00"
            # }
        # We will add the JSON log object to the rules file, NOT overwriting it. 
        # We will write them each inside the object, in order of the timestamps.
        
    main()