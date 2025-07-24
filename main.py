# main.py
import flet as ft
import os
from src.main_app import AppUI

async def main(page: ft.Page):
    """Initializes and runs the Flet application."""
    page.title = "Phone Controller"
    page.window.width = 700
    page.window.height = 700
    page.theme_mode = ft.ThemeMode.DARK

    app_ui = AppUI(page)
    
    app_ui.app_logic.load_scripts()
    page.add(app_ui)
    
    await app_ui.app_logic.scan_devices()

if __name__ == "__main__":
    ft.app(target=main)