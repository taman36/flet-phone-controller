# main.py
import flet as ft
import os
from src.main_app import AppUI

def ensure_sample_script_exists():
    """Checks for the assets/scripts directory and a sample script, creating them if not found."""
    assets_dir = "assets"
    script_dir = os.path.join(assets_dir, "scripts")
    if not os.path.exists(script_dir):
        os.makedirs(script_dir)
        print(f"Created directory: {script_dir}")
        
    sample_script_path = os.path.join(script_dir, "script1_instagram_reels.py")
    if not os.path.exists(sample_script_path):
        # The content for the sample automation script
        script1_content = """
import uiautomator2 as u2
import sys
import time
import random

def main(device_id):
    try:
        should_like = "--like" in sys.argv
        print(f"[{device_id}] Script started. Auto-liking is {'ENABLED' if should_like else 'DISABLED'}.")

        d = u2.connect(device_id)
        package_name = "com.instagram.android"
        
        print(f"[{device_id}] Launching Instagram...")
        d.app_stop(package_name)
        time.sleep(2)
        d.app_start(package_name, stop=True)
        
        reels_tab_selector = d(description="Reels")
        if not reels_tab_selector.wait(timeout=20.0):
            print(f"[{device_id}] Reels tab not found. Exiting.")
            return

        reels_tab_selector.click()
        time.sleep(5)

        width, height = d.window_size()
        
        while True:
            start_x, start_y = width // 2, height * 0.8
            end_y = height * 0.2
            
            print(f"[{device_id}] Swiping to next video...")
            d.swipe(start_x, start_y, start_x, end_y, duration=0.5)
            
            time.sleep(random.uniform(1, 2))

            if should_like and random.random() < 0.8:
                print(f"[{device_id}] Liking video...")
                d.double_click(width // 2, height // 2)
            
            wait_time = random.uniform(4, 8) 
            print(f"[{device_id}] Watching video for {wait_time:.1f}s...")
            time.sleep(wait_time)

    except KeyboardInterrupt:
        print(f"[{device_id}] Script stopped by user.")
    except Exception as e:
        print(f"[{device_id}] An error occurred: {e}")
    finally:
        print(f"[{device_id}] Script finished.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script1_instagram_reels.py <device_id> [--like]")
        sys.exit(1)
    main(sys.argv[1])
"""
        with open(sample_script_path, "w", encoding="utf-8") as f:
            f.write(script1_content)
        print(f"Created sample script file: {sample_script_path}")

async def main(page: ft.Page):
    """Initializes and runs the Flet application."""
    page.title = "Phone Controller"
    page.window.width = 700
    page.window.height = 700
    page.theme_mode = ft.ThemeMode.DARK

    ensure_sample_script_exists()

    app_ui = AppUI(page)
    
    app_ui.app_logic.load_scripts()
    page.add(app_ui)
    
    await app_ui.app_logic.scan_devices()

if __name__ == "__main__":
    ft.app(target=main)