# src/ui_components.py
import flet as ft
import asyncio
import sys
import os
from typing import TYPE_CHECKING

# Use TYPE_CHECKING to prevent circular import errors with AppLogic
if TYPE_CHECKING:
    from .main_app import AppLogic

if hasattr(sys, '_MEIPASS'):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class DeviceControl(ft.Row):
    """A UI control representing a single device row."""
    def __init__(self, device_id: str, app_logic: 'AppLogic'):
        self.device_id = device_id
        self.app_logic = app_logic
        self.running_task = None
        self.running_process = None

        self.checkbox = ft.Checkbox(
            value=False,
            on_change=self.app_logic.update_selected_count
        )
        self.device_id_text = ft.Text(self.device_id, expand=True)
        self.status_indicator = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=False)
        self.play_button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW_ROUNDED,
            on_click=self.toggle_script,
            tooltip="Run script"
        )
        
        super().__init__(
            controls=[
                self.checkbox,
                self.device_id_text,
                ft.Row(controls=[self.status_indicator, self.play_button], spacing=5)
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

    @property
    def is_running(self):
        return self.running_task is not None and not self.running_task.done()

    async def toggle_script(self, e):
        if self.is_running:
            await self.stop_script()
        else:
            selected_script = self.app_logic.get_selected_script()
            if selected_script and selected_script in self.app_logic.available_scripts:
                await self.start_script(selected_script)
            else:
                await self.app_logic.show_snackbar("Please select a valid script!")

    async def start_script(self, script_filename):
        await self.update_ui_for_running_state()
        self.running_task = asyncio.create_task(self.run_script_async(script_filename, self.device_id))

    async def stop_script(self):
        print(f"[{self.device_id}] Requesting stop...")
        if self.running_process:
            try:
                self.running_process.terminate()
                await self.running_process.wait()
            except ProcessLookupError:
                pass 
        if self.running_task:
            self.running_task.cancel()
        await self._kill_atx_agent()
        await self.update_ui_for_stopped_state()

    async def _kill_atx_agent(self):
        print(f"[{self.device_id}] Stopping atx-agent...")
        try:
            await asyncio.create_subprocess_exec(
                'adb', '-s', self.device_id, 'shell', 'pkill', 'atx-agent',
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
        except Exception as e:
            print(f"Error while stopping atx-agent on {self.device_id}: {e}")

    async def run_script_async(self, script_filename, device_id):
        script_path = os.path.join(BASE_DIR, "assets/scripts", script_filename)
        args = ["python", script_path, device_id, "--run-script"]

        try:
            print(f"[{device_id}] Executing: {' '.join(args)}")
            self.running_process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            async for line in self.running_process.stdout:
                print(f"[{device_id}|SCRIPT] {line.decode().strip()}")
            await self.running_process.wait()
            if self.running_process.returncode != 0:
                stderr_output = await self.running_process.stderr.read()
                print(f"[{device_id}] Script finished with error:\n{stderr_output.decode()}")
        except asyncio.CancelledError:
            print(f"[{device_id}] Task was cancelled.")
        except Exception as e:
            print(f"Error running script on {device_id}: {e}")
        finally:
            self.running_task = None
            self.running_process = None
            await self.update_ui_for_stopped_state()

    async def update_ui_for_running_state(self):
        self.play_button.icon = ft.Icons.STOP_ROUNDED
        self.play_button.tooltip = "Stop script"
        self.status_indicator.visible = True
        self.checkbox.disabled = True
        self.update()

    async def update_ui_for_stopped_state(self):
        self.play_button.icon = ft.Icons.PLAY_ARROW_ROUNDED
        self.play_button.tooltip = "Run script"
        self.status_indicator.visible = False
        self.checkbox.disabled = False
        self.update()