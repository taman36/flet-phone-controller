# src/main_app.py
import flet as ft
import asyncio
import os
from .ui_components import DeviceControl

class AppLogic:
    """Handles the main application state and business logic."""
    def __init__(self, page: ft.Page, progress_ring: ft.ProgressRing):
        self.page = page
        self.progress_ring = progress_ring
        self.available_scripts = []
        
        self.device_list_view = ft.ListView(expand=True, spacing=5, auto_scroll=True)
        self.script_dropdown = ft.Dropdown(
            hint_text="Select a script",
            options=[],
            expand=True,
        )
        self.selected_count_text = ft.Text("0 devices selected")
        self.snack_bar = ft.SnackBar(content=ft.Text(""), duration=2000)
        self.page.overlay.append(self.snack_bar)

    def load_scripts(self):
        """Finds script files in the 'assets/scripts' directory."""
        script_dir = os.path.join("assets", "scripts")
        print(f"Looking for scripts in '{script_dir}'...")
        self.available_scripts.clear()
        
        if not os.path.isdir(script_dir):
            print(f"Warning: Directory not found: '{script_dir}'")
            return
            
        for filename in os.listdir(script_dir):
            if filename.endswith('.py'):
                self.available_scripts.append(filename)
                print(f"Found script: {filename}")
        
        self.script_dropdown.options = [ft.dropdown.Option(s) for s in self.available_scripts]

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
        self.page.update()

class AppUI(ft.Column):
    """Constructs the main user interface."""
    def __init__(self, page: ft.Page):
        self.progress_ring = ft.ProgressRing(visible=False, width=16, height=16, stroke_width=2)
        self.app_logic = AppLogic(page, self.progress_ring)

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
            content=ft.Row([self.app_logic.selected_count_text]),
            padding=ft.padding.symmetric(vertical=3, horizontal=15),
            border=ft.border.only(top=ft.border.BorderSide(1, ft.Colors.OUTLINE))
        )
        
        super().__init__(
            controls=[
                toolbar,
                ft.Container(
                    content=self.app_logic.device_list_view,
                    expand=True, padding=10
                ),
                status_bar,
            ],
            expand=True, spacing=0
        )