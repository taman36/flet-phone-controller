import flet as ft
import os
import sys
from src.main_app import AppUI

if hasattr(sys, '_MEIPASS'):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main(page: ft.Page):
    page.title = "InstaPilot"
    page.window.width = 600
    page.window.height = 700
    page.window.resizable = True
    page.theme_mode = ft.ThemeMode.DARK
    page.window.icon = os.path.join(BASE_DIR, "assets/instapilot_logo.ico")
    page.add(
        ft.Row([
            ft.Image(src=os.path.join(BASE_DIR, "assets/instapilot_logo.svg"), width=48, height=48),
            ft.Text("InstaPilot", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.PINK),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        AppUI(page)
    )

if __name__ == "__main__":
    if "--run-script" in sys.argv:
        pass
    else:
        ft.app(target=main)