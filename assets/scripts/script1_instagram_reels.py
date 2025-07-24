import uiautomator2 as u2
import sys
import time
import random
import json
import argparse

def get_script_config():
    """
    Khai báo các tham số cấu hình mà kịch bản này hỗ trợ.
    Hàm này sẽ được ứng dụng Flet gọi để tự động tạo giao diện cài đặt.
    """
    return [
        {
            "name": "min_wait", "label": "Thời gian xem tối thiểu (giây)",
            "type": "number", "default": 4, "min": 1, "max": 60
        },
        {
            "name": "max_wait", "label": "Thời gian xem tối đa (giây)",
            "type": "number", "default": 8, "min": 2, "max": 120
        },
        {
            "name": "like_chance", "label": "Xác suất Thả tim (%)",
            "type": "slider", "default": 80, "min": 0, "max": 100
        },
        {
            "name": "follow_chance", "label": "Xác suất Follow (%)",
            "type": "slider", "default": 5, "min": 0, "max": 100
        }
    ]

def main(args):
    """
    Hàm chính thực thi automation, nhận vào các tham số đã được xử lý.
    """
    try:
        print(f"[{args.device_id}] Script started with enhanced settings.")
        print(f"[{args.device_id}] Wait time: {args.min_wait}-{args.max_wait}s, Like: {args.like_chance}%, Follow: {args.follow_chance}%")

        d = u2.connect(args.device_id)
        # ... (Phần logic khởi động và điều hướng Instagram giữ nguyên) ...

        width, height = d.window_size()
        
        while True:
            # ... (Phần logic vuốt màn hình giữ nguyên) ...
            d.swipe(width//2, int(height*0.8), width//2, int(height*0.2), 0.5)
            
            # Logic Thả tim
            if random.randint(1, 100) <= args.like_chance:
                print(f"[{args.device_id}] Liking video...")
                d.double_click(width // 2, height // 2)
                time.sleep(random.uniform(0.5, 1))

            # Logic Follow (MỚI)
            if random.randint(1, 100) <= args.follow_chance:
                try:
                    # Selector cho nút follow, có thể cần thay đổi
                    follow_button = d(resourceId="com.instagram.android:id/profile_header_follow_button")
                    if follow_button.exists:
                        print(f"[{args.device_id}] Following user...")
                        follow_button.click()
                        time.sleep(random.uniform(1, 2))
                except Exception as e:
                    print(f"[{args.device_id}] Could not perform follow action: {e}")
            
            # Chờ để xem video
            wait_time = random.uniform(args.min_wait, args.max_wait)
            print(f"[{args.device_id}] Watching video for {wait_time:.1f}s...")
            time.sleep(wait_time)

    except KeyboardInterrupt:
        print(f"[{args.device_id}] Script stopped by user.")
    except Exception as e:
        print(f"[{args.device_id}] An error occurred: {e}")
    finally:
        print(f"[{args.device_id}] Script finished.")

if __name__ == "__main__":
    # Nếu được gọi với tham số --get-config, chỉ trả về cấu hình và thoát
    if "--get-config" in sys.argv:
        print(json.dumps(get_script_config()))
        sys.exit(0)

    # Sử dụng argparse để xử lý tham số dòng lệnh một cách chuyên nghiệp
    parser = argparse.ArgumentParser(description="Instagram Reels Automation Script.")
    parser.add_argument("device_id", type=str, help="Device serial ID")
    parser.add_argument("--min-wait", type=float, default=4.0, help="Minimum wait time in seconds.")
    parser.add_argument("--max-wait", type=float, default=8.0, help="Maximum wait time in seconds.")
    parser.add_argument("--like-chance", type=int, default=80, help="Chance to like a video (0-100).")
    parser.add_argument("--follow-chance", type=int, default=5, help="Chance to follow the user (0-100).")
    
    args = parser.parse_args()
    main(args)