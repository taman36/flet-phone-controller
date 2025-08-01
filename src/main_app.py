# src/main_app.py
import flet as ft
import asyncio
import os
import sys
import yaml
from src.ui_components import DeviceControl

if hasattr(sys, '_MEIPASS'):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(BASE_DIR, "assets/scripts/config.yaml")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)

class AppLogic:
    """Handles the main application state and business logic."""
    def __init__(self, page: ft.Page, progress_ring: ft.ProgressRing):
        self.page = page
        self.progress_ring = progress_ring
        self.available_scripts = []
        self.script_display_names = {}

        self.device_list_view = ft.ListView(expand=True, spacing=5, auto_scroll=True)
        self.script_dropdown = ft.Dropdown(
            hint_text="Select a script",
            options=[],
            expand=True,
        )
        self.selected_count_text = ft.Text("0 devices selected")
        self.snack_bar = ft.SnackBar(content=ft.Text(""), duration=2000)
        self.page.overlay.append(self.snack_bar)
        self.select_all_button = None

    def load_scripts(self):
        """Finds script files in the 'assets/scripts' directory and loads display names."""
        script_dir = os.path.join("assets", "scripts")
        print(f"Looking for scripts in '{script_dir}'...")
        self.available_scripts.clear()
        self.script_display_names.clear()

        config = load_config()
        if not os.path.isdir(script_dir):
            print(f"Warning: Directory not found: '{script_dir}'")
            return

        for filename in os.listdir(script_dir):
            if filename.endswith('.py'):
                self.available_scripts.append(filename)
                display_name = config.get(filename, {}).get("DISPLAY_NAME", filename)
                self.script_display_names[filename] = display_name
                print(f"Found script: {filename} ({display_name})")

        # Dropdown: show display name, value is filename
        self.script_dropdown.options = [
            ft.dropdown.Option(key=script, text=self.script_display_names[script])
            for script in self.available_scripts
        ]

    async def scan_devices(self, e=None):
        print("Scanning for ADB devices...")
        self.progress_ring.visible = True
        self.device_list_view.controls.clear()
        self.page.update()
        try:
            proc = await asyncio.create_subprocess_shell(
                'adb devices',
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                lines = stdout.decode().strip().split('\n')
                devices = [line.split('\t')[0] for line in lines[1:] if '\tdevice' in line]
                if not devices:
                    self.device_list_view.controls.append(ft.Text("No devices found.", italic=True, text_align=ft.TextAlign.CENTER))
                else:
                    for device_id in devices:
                        self.device_list_view.controls.append(DeviceControl(device_id, self))
            else:
                self.device_list_view.controls.append(ft.Text(f"ADB Error: {stderr.decode()}", color=ft.Colors.RED))
        except Exception as ex:
            self.device_list_view.controls.append(ft.Text(f"An error occurred: {ex}", color=ft.Colors.RED))
        
        self.progress_ring.visible = False
        await self.update_selected_count()

    async def run_on_selected(self, e):
        selected_script = self.get_selected_script()
        if not selected_script or selected_script not in self.available_scripts:
            await self.show_snackbar("Please select a valid script!")
            return
        
        selected_devices = [c for c in self.device_list_view.controls if isinstance(c, DeviceControl) and c.checkbox.value]
        if not selected_devices:
            await self.show_snackbar("Please select at least one device!")
            return
            
        tasks = [dev.start_script(selected_script) for dev in selected_devices if not dev.is_running]
        await asyncio.gather(*tasks)

    def get_selected_script(self):
        return self.script_dropdown.value

    async def show_snackbar(self, message):
        self.snack_bar.content = ft.Text(message)
        self.snack_bar.open = True
        self.page.update()

    async def update_selected_count(self, e=None):
        controls = self.device_list_view.controls
        total = sum(1 for c in controls if isinstance(c, DeviceControl))
        count = sum(1 for c in controls if isinstance(c, DeviceControl) and c.checkbox.value)
        self.selected_count_text.value = f"{count} / {total} devices selected"
        
        # Toggle select all button text
        if self.select_all_button:
            all_selected = total > 0 and count == total
            self.select_all_button.text = "Deselect All" if all_selected else "Select All"

        self.page.update()

    async def toggle_select_all(self, e):
        controls = self.device_list_view.controls
        total = sum(1 for c in controls if isinstance(c, DeviceControl))
        count = sum(1 for c in controls if isinstance(c, DeviceControl) and c.checkbox.value)
        
        new_value = not (total > 0 and count == total)
        
        for control in controls:
            if isinstance(control, DeviceControl):
                control.checkbox.value = new_value
        await self.update_selected_count()

class AppUI(ft.Column):
    """Constructs the main user interface."""
    def __init__(self, page: ft.Page):
        self.progress_ring = ft.ProgressRing(visible=False, width=16, height=16, stroke_width=2)
        self.app_logic = AppLogic(page, self.progress_ring)
        self.app_logic.select_all_button = ft.TextButton("Select All", on_click=self.app_logic.toggle_select_all)

        # --- Main Tab ---
        toolbar = ft.Container(
            content=ft.Row(
                [
                    self.app_logic.script_dropdown,
                    ft.VerticalDivider(width=10),
                    ft.FilledButton(
                        text="Run on Selected", icon=ft.Icons.PLAY_ARROW,
                        on_click=self.app_logic.run_on_selected,
                    ),
                    ft.VerticalDivider(width=20),
                    self.progress_ring,
                    ft.IconButton(
                        icon=ft.Icons.REFRESH, on_click=self.app_logic.scan_devices,
                        tooltip="Refresh device list"
                    ),
                ],
                spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(vertical=5, horizontal=15),
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.OUTLINE))
        )
        status_bar = ft.Container(
            content=ft.Row([
                self.app_logic.selected_count_text,
                self.app_logic.select_all_button
            ]),
            padding=ft.padding.symmetric(vertical=3, horizontal=15),
            border=ft.border.only(top=ft.border.BorderSide(1, ft.Colors.OUTLINE))
        )
        main_tab = ft.Column([
            toolbar,
            ft.Container(
                content=self.app_logic.device_list_view,
                expand=True, padding=10
            ),
            status_bar,
        ], expand=True, spacing=0)

        # --- Settings Tab ---
        config = load_config()
        fields = {}
        cards = []
        for script, params in config.items():
            display_name = params.get("DISPLAY_NAME", script)
            param_fields = {}
            controls = []
            for key, value in params.items():
                if key == "DISPLAY_NAME":
                    continue  # Don't show DISPLAY_NAME field
                label = key.replace("_", " ").capitalize()
                if isinstance(value, list):
                    field = ft.TextField(
                        label=f"{label} (separate by ';')",
                        value=";".join(value),
                        multiline=True,
                        width=400,
                        label_style=ft.TextStyle(color=ft.Colors.BLACK),
                        text_style=ft.TextStyle(color=ft.Colors.RED)
                    )
                else:
                    field = ft.TextField(
                        label=label,
                        value=str(value),
                        width=400,
                        label_style=ft.TextStyle(color=ft.Colors.BLACK),
                        text_style=ft.TextStyle(color=ft.Colors.RED)
                    )
                param_fields[key] = field
                controls.append(field)
            fields[script] = param_fields
            cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(display_name, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                            *controls
                        ], spacing=10),
                        padding=20,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        width=450
                    ),
                    elevation=3,
                    margin=10
                )
            )

        def on_save(e):
            for script, params in fields.items():
                for key, field in params.items():
                    value = field.value
                    if isinstance(config[script][key], float):
                        try:
                            value = float(value)
                        except:
                            value = config[script][key]
                    elif isinstance(config[script][key], int):
                        try:
                            value = int(value)
                        except:
                            value = config[script][key]
                    elif isinstance(config[script][key], list):
                        value = [x.strip() for x in value.split(";") if x.strip()]
                    config[script][key] = value
            save_config(config)
            page.snack_bar = ft.SnackBar(ft.Text("Settings saved!"))
            page.snack_bar.open = True
            page.update()

        settings_tab = ft.Column([
            ft.Text("Edit script parameters", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
            ft.Divider(),
            ft.Row(cards, wrap=True, spacing=20, run_spacing=20),
            ft.ElevatedButton("Save settings", icon=ft.Icons.SAVE, on_click=on_save)
        ], scroll="always", expand=True)

        # --- Tabs Layout ---
        super().__init__(
            controls=[
                ft.Tabs(
                    selected_index=0,
                    tabs=[
                        ft.Tab(text="Main", content=main_tab),
                        ft.Tab(text="Settings", content=settings_tab),
                    ],
                    expand=1
                )
            ],
            expand=True
        )

        self.app_logic.load_scripts()