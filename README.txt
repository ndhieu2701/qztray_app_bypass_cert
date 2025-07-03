hướng dẫn tạo key cho qz tray:
- private key:
openssl genrsa -out private.key 2048                                          
- public key:
openssl req -new -x509 -key private.key -out public-cert.pem -days 3650 -subj "//CN=QZTray Demo Cert"

