# Matcha Telegram Bot — Bước 1: Deploy khung bot (chưa tích hợp AI)

Bot chạy ở chế độ **polling** (không cần domain/HTTPS/webhook), phù hợp để deploy nhanh và test trước khi tích hợp RAG/LLM.

## 1. Tạo bot qua BotFather

1. Mở Telegram, chat với [@BotFather](https://t.me/BotFather).
2. Gõ `/newbot`, đặt tên và username cho bot (username phải kết thúc bằng `bot`, ví dụ `matcha_tuvan_bot`).
3. BotFather trả về một **token** dạng `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` — lưu lại, đây là bí mật, không commit vào git.

## 2. Cấu hình

```bash
cd bot
cp .env.example .env
# Mở .env, dán token vào biến BOT_TOKEN
```

## 3. Chạy local (không cần Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

Sau khi log hiện `Bot đang chạy ở chế độ polling...`, mở Telegram, tìm bot vừa tạo, gõ `/start` để test.

## 4. Chạy bằng Docker (khuyến nghị khi deploy lên VPS)

```bash
cd bot
docker compose up -d --build
docker compose logs -f
```

## 5. Kiểm tra hoạt động

- Gửi `/start` → bot chào và giới thiệu.
- Gửi `/help` → bot hiện hướng dẫn.
- Gửi câu hỏi bất kỳ (vd: "Nhiệt độ nước pha matcha bao nhiêu?") → bot echo lại tin nhắn kèm ghi chú "sẽ tích hợp AI ở bước tiếp theo".

## 6. Bước tiếp theo (chưa làm ở bước này)

- Thay hàm `generate_reply()` trong [app/handlers.py](app/handlers.py) bằng lời gọi RAG + LLM (Groq API hoặc Ollama local) theo thiết kế trong [../design-opensource.md](../design-opensource.md).
- Thêm Redis để lưu session/ngữ cảnh hội thoại nhiều lượt.
- Thêm CI/CD (Woodpecker/GitHub Actions) để tự động build & deploy khi push code.

## 7. Deploy lên VPS free (khuyến nghị nếu mạng local chặn Telegram)

> **Vì sao cần bước này**: một số mạng công ty/tổ chức chặn hoặc soi (SSL-inspect) traffic tới `api.telegram.org`, khiến bot báo lỗi `CERTIFICATE_VERIFY_FAILED` dù code hoàn toàn đúng. Cách xử lý an toàn nhất là chạy bot trên một máy chủ không bị chặn, thay vì tắt xác thực SSL (không an toàn).

### 7.1. Tạo VPS miễn phí (Oracle Cloud Always Free Tier)

1. Đăng ký tài khoản tại [oracle.com/cloud/free](https://www.oracle.com/cloud/free/) (cần thẻ để xác minh nhưng gói Always Free không bị trừ tiền).
2. Vào **Compute → Instances → Create Instance**.
3. Chọn image **Ubuntu 22.04/24.04**, shape thuộc nhóm **Always Free** (VM.Standard.A1.Flex hoặc VM.Standard.E2.1.Micro).
4. Tải về SSH key được cấp (hoặc dùng key có sẵn của bạn), ghi nhớ **Public IP**.

### 7.2. Cài Docker trên VPS

SSH vào VPS rồi chạy:

```bash
ssh -i /path/to/key ubuntu@<PUBLIC_IP>

# Trên VPS:
sudo apt update && sudo apt install -y ca-certificates curl gnupg
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

### 7.3. Đưa code lên VPS

Từ máy dev (thư mục `bot/`):

```bash
rsync -avz --exclude '.venv' --exclude '__pycache__' \
  -e "ssh -i /path/to/key" \
  ./ ubuntu@<PUBLIC_IP>:~/matcha-bot/
```

(Nếu dùng Git: đơn giản hơn là `git clone` repo trực tiếp trên VPS, miễn là không commit file `.env`.)

### 7.4. Chạy bot trên VPS

```bash
ssh -i /path/to/key ubuntu@<PUBLIC_IP>
cd ~/matcha-bot
cp .env.example .env   # điền BOT_TOKEN
docker compose up -d --build
docker compose logs -f
```

Vì Oracle Cloud không nằm sau proxy chặn Telegram, bot sẽ kết nối bình thường. Gửi `/start` trong Telegram để xác nhận.

### 7.5. Lưu ý bảo mật

- Không mở port nào ra ngoài internet cho bot này (polling mode không cần inbound port, chỉ cần outbound HTTPS).
- Trong Oracle Cloud, mặc định Security List đã chặn hết inbound trừ SSH (22) — không cần mở thêm port cho bot polling.
- Giữ file `.env` (chứa `BOT_TOKEN`) ngoài git, đã có `.gitignore` xử lý sẵn.

