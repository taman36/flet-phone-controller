import uiautomator2 as u2
import sys
import time
import random

def main(device_id):
    """
    Automates scrolling through the Instagram Reels feed, with an option to like videos.
    """
    try:
        # Check if the --like flag was passed from the command line
        should_like = "--like" in sys.argv
        print(f"[{device_id}] Script started. Auto-liking is {'ENABLED' if should_like else 'DISABLED'}.")

        # 1. Connect to the device
        print(f"[{device_id}] Connecting to device...")
        d = u2.connect(device_id)
        
        package_name = "com.instagram.android"
        
        # 2. Launch the application
        print(f"[{device_id}] Force stopping and launching Instagram...")
        d.app_stop(package_name)
        time.sleep(2)
        d.app_start(package_name, stop=True)
        
        # 3. Navigate to the Reels tab
        # The selector might need adjustment based on device language or app version.
        print(f"[{device_id}] Waiting for Reels tab to appear...")
        reels_tab_selector = d(description="Reels")
        if not reels_tab_selector.wait(timeout=20.0):
            print(f"[{device_id}] Reels tab not found. Exiting.")
            return

        reels_tab_selector.click()
        time.sleep(5)

        # 4. Start the main scroll and like loop
        print(f"[{device_id}] Starting scroll loop...")
        width, height = d.window_size()
        
        while True:
            # Define swipe coordinates from 80% to 20% of the screen height
            start_x, start_y = width // 2, int(height * 0.8)
            end_y = int(height * 0.2)
            
            print(f"[{device_id}] Swiping to next video...")
            d.swipe(start_x, start_y, start_x, end_y, duration=0.5)
            
            # Wait a moment before deciding to like
            time.sleep(random.uniform(1, 2))

            # Like the video with an 80% probability to appear more human
            if should_like and random.random() < 0.8:
                print(f"[{device_id}] Liking video...")
                d.double_click(width // 2, height // 2)
            
            # Wait a random duration to simulate watching the video
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