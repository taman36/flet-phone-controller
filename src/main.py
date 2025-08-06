import flet as ft
import uiautomator2 as u2
import yaml
import pyotp
import os
import sys
from src.main_app import AppUI

if hasattr(sys, '_MEIPASS'):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main(page: ft.Page):
    page.title = "AutoPilot"
    page.window.width = 600
    page.window.height = 700
    page.window.resizable = True
    page.theme_mode = ft.ThemeMode.DARK
    page.window.icon = os.path.join(BASE_DIR, "assets/autopilot_logo.ico")
    page.add(
        ft.Row([
            ft.Image(src=os.path.join(BASE_DIR, "assets/autopilot_logo.svg"), width=48, height=48),
            ft.Text("AutoPilot", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.PINK),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        AppUI(page)
    )

if __name__ == "__main__":
    # When the packaged app is called to run a script, it re-launches itself
    # with the --run-script flag. This block handles that execution.
    if "--run-script" in sys.argv:
        try:
            # Find the script path and device_id from the command line arguments
            # Expected format: InstaPilot.exe -u <script_path> <device_id> --run-script
            run_script_index = sys.argv.index("--run-script")
            script_path = sys.argv[run_script_index - 2]
            device_id = sys.argv[run_script_index - 1]

            # IMPORTANT: We will now directly call the script's main function
            # with the device_id as an argument. The user will ensure all
            # scripts conform to the `def main(device_id):` signature.
            
            # Dynamically import and run the script's main() function
            # This allows the packaged exe to behave like the python interpreter
            import importlib.util
            
            # Create a module name from the filename
            module_name = os.path.splitext(os.path.basename(script_path))[0]
            
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            script_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(script_module)
            
            # Call the script's main function directly with the device_id
            script_module.main(device_id)
            
        except Exception as e:
            print(f"Failed to execute script: {e}")
            # Write to a log file for debugging in packaged app
            with open("script_runner_error.log", "w") as f:
                f.write(f"Error: {e}\n")
                f.write(f"Args: {sys.argv}\n")
            sys.exit(1)
    else:
        # If no --run-script flag, launch the main Flet GUI
        ft.app(target=main)