import uiautomator2 as u2
import sys
import time
import random

# ===================================================================
# SCRIPT PARAMETERS
# ===================================================================
MIN_WATCH_TIME_S = 4.0      # Minimum watch time in seconds
MAX_WATCH_TIME_S = 8.0      # Maximum watch time in seconds
LIKE_CHANCE_PERCENT = 75    # 75% chance to like the video
FOLLOW_CHANCE_PERCENT = 50   # 5% chance to follow if a follow button is visible
VIDEOS_TO_SCROLL = 50       # Stop after scrolling this many videos
COMMENT_CHANCE_PERCENT = 50  # 10% chance to leave a comment
COMMENT_LIST = [           # List of comments to choose from randomly
    "Great video!",
    "Love this!",
    "Very Good",
    "So cool.",
    "Nice one"
]
# ===================================================================

def main(device_id):
    """Main script logic for controlling the device."""
    print(f"[{device_id}] Starting Instagram Reels script...")
    print(f"[{device_id}] Settings: Watch {MIN_WATCH_TIME_S}-{MAX_WATCH_TIME_S}s | Like {LIKE_CHANCE_PERCENT}% | Follow {FOLLOW_CHANCE_PERCENT}% | Scroll {VIDEOS_TO_SCROLL} videos")

    try:
        # Connect to the device
        d = u2.connect(device_id)
        package_name = "com.instagram.android"

        # Launch Instagram
        print(f"[{device_id}] Opening Instagram...")
        d.app_start(package_name, stop=True)

        # Navigate to the Reels tab
        print(f"[{device_id}] Navigating to Reels tab...")
        reels_tab_selector = d(description="Reels")
        if not reels_tab_selector.wait(timeout=20.0):
            print(f"[{device_id}] ERROR: Reels tab not found. Stopping script.")
            return
        reels_tab_selector.click()
        time.sleep(3) # Wait for the first video to load

        # Get screen dimensions for swiping
        width, height = d.window_size()
        start_x = width // 2
        start_y = height * 0.8
        end_y = height * 0.2

        # Start the limited scroll loop
        print(f"[{device_id}] Starting scroll loop for {VIDEOS_TO_SCROLL} videos...")
        for i in range(VIDEOS_TO_SCROLL):
            print(f"[{device_id}] Video {i + 1}/{VIDEOS_TO_SCROLL}...")

            #Check for ads before performing any actions
            if d(description="Sponsored").exists:
                print(f"[{device_id}] -> Ad detected, skipping.")
                d.swipe(start_x, start_y, start_x, end_y, duration=0.5)
                time.sleep(random.uniform(1, 2))
                continue # Skip to the next video

            # 1. Like action
            if random.randint(1, 100) <= LIKE_CHANCE_PERCENT:
                print(f"[{device_id}] -> Liking video...")
                d.double_click(start_x, height / 2, duration=0.1)

            # 2. Follow action
            if random.randint(1, 100) <= FOLLOW_CHANCE_PERCENT:
                try:
                    follow_button = d(text="Follow")
                    if follow_button.exists:
                        follow_button.click()
                        time.sleep(1.5) # Wait for potential pop-up

                        # If collaborator pop-up appears, press back
                        if d(resourceId="com.instagram.android:id/layout_container_bottom_sheet").exists:
                            d.press("back")
                except Exception:
                    pass

            # 3. Watch video
            watch_time = random.uniform(MIN_WATCH_TIME_S, MAX_WATCH_TIME_S)
            print(f"[{device_id}] Watching for {watch_time:.1f}s...")
            time.sleep(watch_time)

            # 4. Comment action
            if random.randint(1, 100) <= COMMENT_CHANCE_PERCENT:
                print(f"[{device_id}] -> Attempting to comment...")
                try:
                    # Click the comment icon
                    d(description="Comment").click()
                    time.sleep(2) # Wait for comment section to open

                    # Select a random comment and post it
                    comment_text = random.choice(COMMENT_LIST)
                    d(resourceId="com.instagram.android:id/layout_comment_thread_edittext").set_text(comment_text)
                    d(description="Post").click()
                    print(f"[{device_id}] -> Commented: '{comment_text}'")
                    time.sleep(2.5) # Wait for comment to post

                    # Press back to close the comment section
                    d.press("back")
                    time.sleep(1)
                    d.press("back")
                    time.sleep(2)

                except Exception:
                    print(f"[{device_id}] -> Failed to comment, pressing back to recover.")
                    # In case of any error, press back to avoid getting stuck
                    d.press("back")
                    pass

            # 5. Swipe to the next video
            print(f"[{device_id}] Swiping to next video...")
            d.swipe(start_x, start_y, start_x, end_y, duration=0.5)
            time.sleep(random.uniform(1, 2))

        print(f"[{device_id}] Scroll target of {VIDEOS_TO_SCROLL} videos reached.")

    except KeyboardInterrupt:
        print(f"[{device_id}] Script stopped by user.")
    except Exception as e:
        print(f"[{device_id}] An unexpected error occurred: {e}")
    finally:
        print(f"[{device_id}] Script finished.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <device_id>")
        sys.exit(1)
    
    device_serial = sys.argv[1]
    main(device_serial)