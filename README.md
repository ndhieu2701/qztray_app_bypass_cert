app bypass qztray để silent print
- b1: trước tiên cài đặt qztray v2.2.5
- b2: tạo private key và public key trong file readme.txt
- b3: add public key vào trong qztray để làm key verify cho qztray
- b4: chạy app này

app có 2 phiên bản: 1 file exe duy nhất và 1 file exe cùng các folder kèm theo để khởi động nhanh hơn
hướng dẫn cài đặt:
- chạy file .exe là hoàn thành

sau khi mở app sẽ phải chọn đường dẫn đến publick key và private key để app lưu lại, khi đó app sẽ tạo ra 1 file config.json để lưu lại, nếu bật chức năng khởi động cùng window nó sẽ lấy config từ file đó điền vào app, bạn không phải làm gì cả

hướng dẫn build:
- cài đặt thư viện cần thiết: pip install -r requirements.txt
- bản 1 file .exe:  pyinstaller --onefile --noconsole  --add-data "ReadFile.ico;." --add-data "ReadFile.png;." qz_cert_tray_helper.py
- bản 1 file .exe và folder tài nguyên: pyinstaller --noconsole --onedir --icon=ReadFile.ico --add-data "ReadFile.ico;." qz_cert_tray_helper_v2.py

app sẽ cung cấp 2 api: chỉ cần app bạn gọi api tới "http://localhost:5000"
- "/publick-key": lấy thông tin public key từ file config
- "/sign": lấy signature cho qztray sign thông tin gửi tới máy để in