import uiautomator2 as u2
import sys
import time
import random
import itertools

# ===================================================================
# SCRIPT PARAMETERS
# ===================================================================
SEARCH_USER = "realdonaldtrump"
MIN_WATCH_TIME_S = 4.0
MAX_WATCH_TIME_S = 8.0
LIKE_CHANCE_PERCENT = 75
FOLLOW_CHANCE_PERCENT = 50
VIDEOS_TO_SCROLL = 50
COMMENT_CHANCE_PERCENT = 50
COMMENT_LIST = [
    "Great video!",
    "Love this!",
    "Very Good",
    "So cool.",
    "Nice one"
]
# ===================================================================

def main(device_id):
    """Main script logic for controlling the device."""
    print(f"[{device_id}] Starting Instagram 'Search & Reel' script for keyword: '{SEARCH_USER}'")

    try:
        d = u2.connect(device_id)
        package_name = "com.instagram.android"
        d.app_start(package_name, stop=True)

        print(f"[{device_id}] Navigating to search...")
        d(description="Search and explore").click(timeout=20.0)

        print(f"[{device_id}] Searching for keyword...")
        d(resourceId="com.instagram.android:id/action_bar_search_edit_text").set_text(SEARCH_USER)
        d.press("enter")
        time.sleep(4)

        print(f"[{device_id}] Switching to Reels tab for the keyword...")
        reels_search_tab = d(text="Accounts")
        if not reels_search_tab.exists:
            print(f"[{device_id}] ERROR: 'Reels' tab not found in search results.")
            return
        reels_search_tab.click()
        time.sleep(3)
        #Click on first account matched
        d(resourceId="com.instagram.android:id/row_search_user_username")[0].click()
        time.sleep(2)
        d(resourceId="com.instagram.android:id/profile_tab_icon_view")[1].click()
        time.sleep(2)
        d(resourceId="com.instagram.android:id/preview_clip_thumbnail")[0].click()
        time.sleep(2)

        width, height = d.window_size()
        
        # Create an iterator that cycles through the comment list endlessly
        comment_cycler = itertools.cycle(COMMENT_LIST)

        print(f"[{device_id}] Starting action loop for {VIDEOS_TO_SCROLL} videos...")
        for i in range(VIDEOS_TO_SCROLL):
            print(f"[{device_id}] Video {i + 1}/{VIDEOS_TO_SCROLL}...")

            if d(description="Sponsored").exists:
                print(f"[{device_id}] -> Ad detected, skipping.")
                d.swipe_ext("up", 0.8)
                continue

            if random.randint(1, 100) <= LIKE_CHANCE_PERCENT:
                d.double_click(width / 2, height / 2, duration=0.1)

            if random.randint(1, 100) <= FOLLOW_CHANCE_PERCENT:
                try:
                    if d(text="Follow").exists:
                        d(text="Follow").click()
                        time.sleep(1.5)
                        if d(resourceId="com.instagram.android:id/layout_container_bottom_sheet").exists:
                            d.press("back")
                except Exception:
                    pass

            time.sleep(random.uniform(MIN_WATCH_TIME_S, MAX_WATCH_TIME_S))

            if random.randint(1, 100) <= COMMENT_CHANCE_PERCENT:
                try:
                    d(description="Comment").click()
                    time.sleep(2)
                    
                    # Get the next comment from the cycler
                    comment_text = next(comment_cycler)
                    
                    d(resourceId="com.instagram.android:id/layout_comment_thread_edittext").set_text(comment_text)
                    d(description="Post").click()
                    time.sleep(2.5)
                    d.press("back")
                    time.sleep(1)
                    d.press("back")
                except Exception:
                    if d(resourceId="com.instagram.android:id/layout_comment_thread_edittext").exists:
                        d.press("back")
                    pass

            d.swipe_ext("up", 0.8)
            time.sleep(random.uniform(1, 2))

        print(f"[{device_id}] Action loop finished after {VIDEOS_TO_SCROLL} videos.")

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