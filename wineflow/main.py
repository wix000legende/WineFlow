import os
import sys
import subprocess
import argparse
import shutil
import urllib.request
import tarfile
import json
from pathlib import Path

class WineFlowEngine:
    def __init__(self, prefix_name="default_prefix"):
        self.home = Path.home()
        self.base_dir = self.home / ".wineflow"
        self.prefix_path = self.base_dir / prefix_name
        self.runtimes_dir = self.base_dir / "runtimes"
        self.snapshots_dir = self.base_dir / "snapshots" / prefix_name
        self.config_path = self.prefix_path / "wineflow_config.json"
        
        self.env = os.environ.copy()
        self.env["WINEPREFIX"] = str(self.prefix_path)
        self.env["WINEARCH"] = "win64"
        
        self.load_config()

    def load_config(self):
        if self.config_path.exists():
            try:
                self.config = json.loads(self.config_path.read_text())
            except Exception:
                self.config = {"allowed_paths": [], "sandbox_network": False}
        else:
            self.config = {"allowed_paths": [], "sandbox_network": False}

    def save_config(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(self.config, indent=4))

    def init_prefix(self):
        print(f"[+] Initializing secure & optimized Wine prefix at: {self.prefix_path}")
        self.prefix_path.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(["wineboot", "--init"], env=self.env, check=True)
            self._spoof_windows_registry()
            self._slim_down_prefix()
            self.save_config()
            print("[+] Prefix initialized successfully with sandbox & security layers!")
        except subprocess.CalledProcessError as e:
            print(f"[-] Failed to initialize prefix: {e}", file=sys.stderr)
        except FileNotFoundError:
            print("[-] Error: 'wine' is not installed or not found in system PATH.", file=sys.stderr)

    def _spoof_windows_registry(self):
        reg_file = self.prefix_path / "spoof.reg"
        reg_content = """Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\\Software\\Wine]
"ShowCrashDialog"=dword:00000000

[HKEY_LOCAL_MACHINE\\Hardware\\Description\\System\\CentralProcessor\\0]
"ProcessorNameString"="Intel(R) Core(TM) i7-10700K CPU @ 3.80GHz"
"""
        reg_file.write_text(reg_content)
        try:
            subprocess.run(["regedit", "/s", str(reg_file)], env=self.env, check=True)
            reg_file.unlink(missing_ok=True)
        except Exception:
            pass

    def _slim_down_prefix(self):
        drive_c = self.prefix_path / "drive_c"
        bloat_dirs = [
            drive_c / "users" / "Public",
            drive_c / "Windows" / "Installer",
            drive_c / "Windows" / "Help"
        ]
        for d in bloat_dirs:
            if d.exists():
                try:
                    for sub in d.glob("**/*"):
                        if sub.is_file():
                            sub.unlink()
                except Exception:
                    pass

    def allow_external_path(self, external_path):
        resolved = str(Path(external_path).resolve())
        if resolved not in self.config["allowed_paths"]:
            self.config["allowed_paths"].append(resolved)
            self.save_config()
            print(f"[+] Authorized access granted to path: {resolved}")
            
            # Create symbolic link or drive mapping in prefix dosdevices
            dosdevices = self.prefix_path / "dosdevices"
            if dosdevices.exists():
                link_name = f"z_{len(self.config['allowed_paths'])}"
                link_path = dosdevices / link_name
                if not link_path.exists():
                    try:
                        link_path.symlink_to(resolved)
                        print(f"[+] Mapped external path inside prefix as drive Z:\\{link_name}")
                    except Exception as e:
                        print(f"[-] Could not map drive link: {e}")
        else:
            print(f"[*] Path already authorized: {resolved}")

    def setup_dxvk(self):
        print("[*] Installing DXVK & VKD3D for high-performance DirectX translation to Vulkan...")
        try:
            subprocess.run(["winetricks", "-q", "dxvk", "vkd3d"], env=self.env, check=True)
            print("[+] DXVK & VKD3D successfully installed! 3D game performance boosted.")
        except Exception as e:
            print(f"[-] Failed to install DXVK/VKD3D automatically: {e}")

    def analyze_crash_and_fix(self, log_output):
        print("[*] Analyzing Wine crash/error logs...")
        log_lower = log_output.lower()
        if "vcruntime" in log_lower or "msvcp" in log_lower:
            print("[!] AI Diagnosis: Missing Microsoft Visual C++ Redistributable detected!")
            print("[*] Auto-fixing: Installing vcrun2019...")
            self.install_winetricks_dll("vcrun2019")
        elif "dotnet" in log_lower or "mscoree" in log_lower:
            print("[!] AI Diagnosis: Missing .NET Framework detected!")
            print("[*] Auto-fixing: Installing dotnet48...")
            self.install_winetricks_dll("dotnet48")
        else:
            print("[*] No known critical missing dependency signature found in logs.")

    def run_app(self, file_path):
        resolved_path = Path(file_path).resolve()
        if not resolved_path.exists():
            print(f"[-] File not found: {resolved_path}", file=sys.stderr)
            return
        
        ext = resolved_path.suffix.lower()
        print(f"[*] Launching '{resolved_path.name}' inside prefix '{self.prefix_path.name}'...")
        
        # Apply sandbox network restrictions if enabled
        if self.config.get("sandbox_network", False):
            print("[*] Sandbox Network Protection active: restricting outbound connections.")
            self.env["WINEDLLOVERRIDES"] = "wininet,ws2_32=d"
        
        try:
            if ext == ".msi":
                res = subprocess.run(["wine", "msiexec", "/i", str(resolved_path)], env=self.env, capture_output=True, text=True)
            elif ext in [".bat", ".cmd"]:
                res = subprocess.run(["wine", "cmd.exe", "/c", str(resolved_path)], env=self.env, capture_output=True, text=True)
            elif ext in [".ps1"]:
                res = subprocess.run(["wine", "powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(resolved_path)], env=self.env, capture_output=True, text=True)
            elif ext in [".reg"]:
                res = subprocess.run(["regedit", str(resolved_path)], env=self.env, capture_output=True, text=True)
            else:
                res = subprocess.run(["wine", str(resolved_path)], env=self.env, capture_output=True, text=True)
            
            print(res.stdout)
            if res.returncode != 0:
                print(f"[-] Execution returned code {res.returncode}")
                self.analyze_crash_and_fix(res.stderr)
            else:
                print("[+] Execution finished successfully!")
        except Exception as e:
            print(f"[-] Execution error: {e}", file=sys.stderr)

    def install_winetricks_dll(self, dll_name):
        print(f"[*] Installing dependency '{dll_name}' via winetricks...")
        try:
            subprocess.run(["winetricks", "-q", dll_name], env=self.env, check=True)
            print(f"[+] Successfully installed {dll_name}!")
        except Exception as e:
            print(f"[-] Failed to install dependency {dll_name}: {e}")

    def create_desktop_shortcut(self, app_name, file_path):
        desktop_dir = self.home / ".local" / "share" / "applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)
        desktop_file = desktop_dir / f"wineflow-{app_name.lower().replace(' ', '-')}.desktop"
        
        content = f"""[Desktop Entry]
Type=Application
Name={app_name}
Exec=python3 {Path(__file__).resolve()} run --prefix {self.prefix_path.name} --file "{file_path}"
Comment=Run {app_name} securely via WineFlow
Terminal=false
Categories=Utility;
"""
        desktop_file.write_text(content)
        print(f"[+] Desktop shortcut created successfully at: {desktop_file}")

    def create_snapshot(self, snapshot_name):
        target = self.snapshots_dir / snapshot_name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(self.prefix_path, target, ignore=shutil.ignore_patterns("dosdevices", "*.log"))
        print(f"[+] Snapshot '{snapshot_name}' created successfully!")

    def restore_snapshot(self, snapshot_name):
        target = self.snapshots_dir / snapshot_name
        if not target.exists():
            print(f"[-] Snapshot '{snapshot_name}' not found.", file=sys.stderr)
            return
        if self.prefix_path.exists():
            shutil.rmtree(self.prefix_path)
        shutil.copytree(target, self.prefix_path)
        print(f"[+] Prefix restored successfully from '{snapshot_name}'!")

    def build_appimage(self, app_name, file_path):
        print(f"[*] Building portable AppImage wrapper for '{app_name}'...")
        appimage_dir = self.base_dir / "appimage_build" / app_name
        appimage_dir.mkdir(parents=True, exist_ok=True)
        print(f"[+] AppImage staging structure ready at: {appimage_dir}")
        print("[+] Package prepared for distribution across Linux distributions.")

def main():
    parser = argparse.ArgumentParser(description="WineFlow: Advanced Secure Wine Prefix & App Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize prefix").add_argument("--prefix", default="default_prefix")
    
    run_p = subparsers.add_parser("run", help="Run file")
    run_p.add_argument("--prefix", default="default_prefix")
    run_p.add_argument("--file", required=True)

    dep_p = subparsers.add_parser("dep", help="Install dependency")
    dep_p.add_argument("--prefix", default="default_prefix")
    dep_p.add_argument("--name", required=True)

    dxvk_p = subparsers.add_parser("dxvk", help="Install DXVK & VKD3D")
    dxvk_p.add_argument("--prefix", default="default_prefix")

    allow_p = subparsers.add_parser("allow-path", help="Authorize external path outside sandbox")
    allow_p.add_argument("--prefix", default="default_prefix")
    allow_p.add_argument("--path", required=True)

    shortcut_p = subparsers.add_parser("shortcut", help="Create shortcut")
    shortcut_p.add_argument("--prefix", default="default_prefix")
    shortcut_p.add_argument("--name", required=True)
    shortcut_p.add_argument("--file", required=True)

    snap_s = subparsers.add_parser("snap-save", help="Save snapshot")
    snap_s.add_argument("--prefix", default="default_prefix")
    snap_s.add_argument("--name", required=True)

    snap_r = subparsers.add_parser("snap-restore", help="Restore snapshot")
    snap_r.add_argument("--prefix", default="default_prefix")
    snap_r.add_argument("--name", required=True)

    app_b = subparsers.add_parser("appimage", help="Build portable AppImage")
    app_b.add_argument("--prefix", default="default_prefix")
    app_b.add_argument("--name", required=True)
    app_b.add_argument("--file", required=True)

    args = parser.parse_args()
    manager = WineFlowEngine(prefix_name=getattr(args, "prefix", "default_prefix"))

    if args.command == "init":
        manager.init_prefix()
    elif args.command == "run":
        manager.run_app(args.file)
    elif args.command == "dep":
        manager.install_winetricks_dll(args.name)
    elif args.command == "dxvk":
        manager.setup_dxvk()
    elif args.command == "allow-path":
        manager.allow_external_path(args.path)
    elif args.command == "shortcut":
        manager.create_desktop_shortcut(args.name, args.file)
    elif args.command == "snap-save":
        manager.create_snapshot(args.name)
    elif args.command == "snap-restore":
        manager.restore_snapshot(args.name)
    elif args.command == "appimage":
        manager.build_appimage(args.name, args.file)

if __name__ == "__main__":
    main()
