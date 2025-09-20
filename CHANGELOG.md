# Changelog - Flet Phone Controller

## [Updated] - September 18, 2025

### Changed in UI Settings Display

#### Thay đổi hiển thị danh sách trong Settings:
- **Hiển thị mỗi item trên 1 dòng**: Thay vì phân cách bằng `;`, giờ mỗi account/item hiển thị trên một dòng riêng
- **Sử dụng newline (\n) để phân cách**: Thay đổi từ `;` sang `\n` để dễ đọc hơn
- **Cải thiện giao diện**: 
  - Tăng width TextField từ 400 → 600px
  - Tăng min_lines từ 3 → 5, max_lines từ 10 → 15
  - Tăng container width từ 450 → 650px, height từ 400 → 500px
  - Thêm text_style với size=12 cho dễ đọc hơn

#### Chi tiết kỹ thuật:
- File thay đổi: `/src/main_app.py`
- Hàm `open_script_settings()`: 
  - Label thay đổi từ `(separate by ';')` → `(one per line)`
  - Value display: `";".join(value)` → `"\n".join(value)`
  - Parse input: `value.split(";")` → `value.split("\n")`

#### Ví dụ hiển thị trước và sau:
**Trước:**
```
user1|pass1|secret1;user2|pass2|secret2;user3|pass3|secret3
```

**Sau:**
```
user1|pass1|secret1
user2|pass2|secret2  
user3|pass3|secret3
```

---

## [Updated] - September 18, 2025 (v2)

### Changed Login Logic - Smart Account Selection

#### Thay đổi logic login:
- **Tìm account không có IP đầu tiên**: Chỉ sử dụng accounts chưa được đánh dấu (format 3 phần: `username|password|secret`)
- **Mark IP chỉ khi thành công**: Chỉ thêm device_ip vào account khi login thành công
- **Bảo toàn accounts khi thất bại**: Nếu login thất bại, account giữ nguyên format cũ để thử lại

#### Chi tiết kỹ thuật:

1. **Functions mới**:
   - `get_first_account_without_ip()` → Tìm account chưa có IP (3 phần)
   - `mark_account_with_ip(index, ip)` → Đánh dấu IP sau khi login thành công
   - Thay thế `get_and_update_first_account_with_ip()` cũ

2. **Flow mới**:
   ```
   1. Tìm account không có IP đầu tiên
   2. Thử login với account đó
   3. Nếu THÀNH CÔNG → thêm IP vào cuối
   4. Nếu THẤT BẠI → giữ nguyên để thử lại
   ```

3. **Ưu điểm**:
   - Không lãng phí accounts khi login thất bại
   - Có thể retry với cùng account khi cần
   - Theo dõi được accounts nào đã login thành công
   - Thread-safe với file locking

#### Ví dụ:
```yaml
# Ban đầu
ACCOUNTS:
  - "user1|pass1|secret1"          # ← Sẽ được dùng đầu tiên
  - "user2|pass2|secret2" 
  - "user3|pass3|secret3|192.168.1.50"  # ← Bị skip (đã có IP)

# Sau khi login thành công với 192.168.1.100
ACCOUNTS:
  - "user1|pass1|secret1|192.168.1.100"  # ← Đã được mark
  - "user2|pass2|secret2"                # ← Sẽ được dùng lần sau
  - "user3|pass3|secret3|192.168.1.50"
```

---

## [Updated] - September 18, 2025

### Changed in login.py

#### Thay đổi chính:
- **Không xóa account sau khi login**: Trước đây, sau khi login thành công, account sẽ bị xóa khỏi danh sách
- **Thêm IP vào thông tin account**: Bây giờ sau khi login thành công, IP của máy sẽ được thêm vào cuối chuỗi thông tin tài khoản

#### Chi tiết kỹ thuật:

1. **Hàm đã thay đổi**:
   - `get_and_delete_first_account()` → `get_and_update_first_account_with_ip(device_ip)`
   
2. **Logic mới**:
   - Account string format cũ: `username|password|secret`
   - Account string format mới: `username|password|secret|device_ip`
   - Nếu account đã có IP (4 phần), sẽ giữ nguyên
   - Nếu account chưa có IP (3 phần), sẽ thêm IP vào cuối

3. **Ưu điểm**:
   - Theo dõi được account nào đã login trên máy nào
   - Không mất thông tin account sau khi sử dụng
   - Có thể tái sử dụng account cho các lần login sau
   - Dễ debug và track lịch sử login

#### Ví dụ:
```yaml
# Trước khi login
ACCOUNTS:
  - "user1|pass1|secret1"
  - "user2|pass2|secret2"

# Sau khi login thành công với IP 192.168.1.100
ACCOUNTS:
  - "user1|pass1|secret1|192.168.1.100"
  - "user2|pass2|secret2"
```

#### File đã được thay đổi:
- `/assets/scripts/login.py`

#### Tương thích ngược:
- Script vẫn hoạt động với account format cũ (3 phần)
- Tự động chuyển đổi sang format mới (4 phần) sau lần login đầu tiên
