import uiautomator2 as u2
import pyotp
import time
import sys
import os
import yaml
import threading

# --- Thread-safe Account Management Logic (Self-contained) ---

# Global lock to prevent race conditions when multiple scripts access the config file.
config_lock = threading.Lock()

def get_config_path():
    """Determines the correct path to config.yaml, whether in dev or bundled."""
    # This logic ensures the script can find config.yaml from the project root
    # whether it's run directly or as part of a PyInstaller bundle.
    if hasattr(sys, '_MEIPASS'):
        # In bundled app, the base directory is the one containing the executable
        base_dir = os.path.dirname(sys.executable)
    else:
        # In development, go up two levels from /assets/scripts/ to project root
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base_dir, 'assets', 'scripts', 'config.yaml')

def get_and_delete_first_account():
    """
    Atomically reads the config, gets the first account from 'login.py:ACCOUNTS',
    parses it, and writes the updated config back. This is a destructive operation.
    Uses a file-based lock to ensure multi-process safety.
    Returns the first account dictionary or None if no accounts are left.
    """
    config_file = get_config_path()
    lock_file = config_file + ".lock"
    
    # --- Acquire Lock ---
    timeout = 30  # seconds to wait for the lock
    start_time = time.time()
    while True:
        try:
            # Atomically create the lock file. Fails if it already exists.
            lock_fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(lock_fd)
            break # Lock acquired
        except FileExistsError:
            if time.time() - start_time > timeout:
                print(f"[LoginScript] CRITICAL: Timed out waiting for lock file {lock_file}.")
                # As a fallback, try to remove a potentially stale lock file.
                try:
                    os.remove(lock_file)
                    print("[LoginScript] Removed stale lock file.")
                except OSError as e:
                    print(f"[LoginScript] CRITICAL: Could not remove stale lock file: {e}")
                return None # Could not acquire lock
            time.sleep(0.2) # Wait before retrying

    try:
        # --- Safely Modify Config ---
        if not os.path.exists(config_file):
            print(f"[LoginScript] CRITICAL: config.yaml not found at {config_file}")
            return None

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            print(f"[LoginScript] CRITICAL: Failed to read or parse config.yaml: {e}")
            return None

        if (not config 
            or 'login.py' not in config 
            or 'ACCOUNTS' not in config['login.py'] 
            or not isinstance(config['login.py'].get('ACCOUNTS'), list) 
            or not config['login.py']['ACCOUNTS']):
            print("[LoginScript] No accounts found or 'login.py:ACCOUNTS' key is invalid in config.yaml.")
            return None

        account_string = config['login.py']['ACCOUNTS'].pop(0)
        print(f"[LoginScript] Got account string. {len(config['login.py']['ACCOUNTS'])} remaining.")

        try:
            user, pwd, secret = account_string.split('|')
            first_account = {'user': user, 'pass': pwd, 'secret': secret}
        except ValueError:
            print(f"[LoginScript] CRITICAL: Account string '{account_string}' is malformed. Expected 'user|pass|secret'.")
            return None

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        except Exception as e:
            print(f"[LoginScript] CRITICAL: Failed to write updated config.yaml: {e}")
            return None
        
        return first_account

    finally:
        # --- Release Lock ---
        try:
            os.remove(lock_file)
        except OSError as e:
            print(f"[LoginScript] WARNING: Could not remove lock file {lock_file}: {e}")

# --- Main Login Logic ---

def login_instagram(device_ip):
    """
    Logs into Instagram using an account fetched and deleted from config.yaml.
    device_ip: IP of the Android device.
    """
    account = get_and_delete_first_account()
    if not account:
        print(f"[{device_ip}] Could not get an account. Exiting.")
        return False

    try:
        # Extract details from the account object
        username = account['user']
        password = account['pass']
        secret_code = account['secret']
        
        # Connect to the Android device
        print(f"[{device_ip}] Connecting to device...")
        d = u2.connect(device_ip)
        print(f"[{device_ip}] Connected to device.")
        
        # Open Instagram URL
        print(f"[{device_ip}] Opening Instagram")
        d.open_url("https://instagram.com")
        time.sleep(3)

        # Handle the "Open with" dialog if it appears
        d(text="Instagram").click_exists()
        d(resourceId="android:id/button_always").click_exists()

        # Check for the "I already have an account" button
        login_button = d(description="I already have an account")
        if login_button.wait(timeout=5):
            login_button.click()
            time.sleep(2)
        
        # Wait for the "Log in" button to appear
        login_submit = d(description="Log in")
        if not login_submit.wait(timeout=15):
            print(f"[{device_ip}] Could not find 'Log in' button.")
            return False
        
        # Enter username and password
        print(f"[{device_ip}] Entering credentials for {username}")
        edit_texts = d(className="android.widget.EditText")
        if edit_texts.count >= 2:
            edit_texts[0].set_text(username)
            time.sleep(1)
            edit_texts[1].set_text(password)
            time.sleep(1)
        else:
            print(f"[{device_ip}] Did not find enough EditText fields.")
            return False
        
        # Click the "Log in" button
        login_submit.click()
        time.sleep(10)
        if d(text="Try another way").click_exists(timeout=5):
            print(f"[{device_ip}] 'Try another way' button found, clicking it.")
            time.sleep(2) # Giữ lại sleep để chờ màn hình tiếp theo load
            
            # Tìm và nhấp vào "Authentication app"
            if d(text="Authentication app").click_exists(timeout=5):
                # Tìm và nhấp vào nút "Continue"
                d(description="Continue").click_exists(timeout=5)
        
        # Wait for the 2FA screen
        auth_prompt = d(description="Go to your authentication app")
        if auth_prompt.wait(timeout=15):
            print(f"[{device_ip}] Reached 2FA screen.")
            
            # Generate and enter 2FA code
            totp = pyotp.TOTP(secret_code)
            two_fa_code = totp.now()
            print(f"[{device_ip}] Generated 2FA code: {two_fa_code}")
            
            auth_edit_text = d(className="android.widget.EditText")
            if auth_edit_text.wait(timeout=5):
                auth_edit_text.set_text(two_fa_code)
                time.sleep(1)
            else:
                print(f"[{device_ip}] Could not find EditText for 2FA code.")
                return False
            
            # Click the "Continue" button
            continue_button = d(description="Continue")
            if continue_button.wait(timeout=5):
                continue_button.click()
                time.sleep(3)
                
                # Check for 'Save your login info?' popup
                if d(description="Save your login info?").wait(timeout=10):
                    if d(description="Save").wait(timeout=5):
                        d(description="Save").click()
                        time.sleep(2)
                
                print(f"[{device_ip}] Login successful for {username}!")
                return True
            else:
                print(f"[{device_ip}] Could not find 'Continue' button.")
                return False
        else:
            print(f"[{device_ip}] 2FA screen did not appear - username/password might be incorrect.")
            return False
            
    except Exception as e:
        # The account is already deleted, so we just log the error.
        print(f"[{device_ip}] An unexpected error occurred for user {account.get('user')}: {str(e)}")
        return False

def main(device_id):
    try:
        success = login_instagram(device_id)
        if success:
            print(f"--- RESULT: Login Succeeded for {device_id} ---")
        else:
            print(f"--- RESULT: Login Failed for {device_id} ---")
    except Exception as e:
        print(f"--- An error occurred in main: {e} ---")

if __name__ == "__main__":
    """
    Main function for standalone testing of the login script.
    It expects the device_id to be passed as a command-line argument.
    """
    if len(sys.argv) < 2:
        print("Usage: python login.py <device_id>")
        print("Example: python login.py 192.168.1.100")
        sys.exit(1)
        
    device_id = sys.argv[1]
    print(f"--- Running Login Script for Device: {device_id} ---")

    try:
        success = login_instagram(device_id)
        if success:
            print(f"--- RESULT: Login Succeeded for {device_id} ---")
        else:
            print(f"--- RESULT: Login Failed for {device_id} ---")
    except Exception as e:
        print(f"--- An error occurred in main: {e} ---")