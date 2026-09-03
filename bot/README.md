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

## 5. Tích hợp LLM local bằng Ollama

Docker Compose đã chạy sẵn service Ollama và lưu model trong volume `ollama-data`.
Mặc định bot dùng `qwen2.5:3b`, phù hợp hơn với máy khoảng 16 GB RAM và hỗ trợ tiếng Việt.

Sau lần đầu khởi động, tải model:

```bash
docker compose exec ollama ollama pull qwen2.5:3b
```

Có thể đổi model trong `.env`:

```bash
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_TIMEOUT=120
```

Sau khi đổi cấu hình, khởi động lại bot:

```bash
docker compose up -d --build
```

Model `qwen2.5:3b` cần khoảng 2 GB dung lượng. Không nên tải nhiều model nếu VPS còn ít ổ đĩa.

## 6. RAG với Qdrant

Compose đã chạy thêm Qdrant và lưu dữ liệu trong volume `qdrant-data`. Tài liệu nguồn nằm trong thư mục `knowledge/`. Sau khi thêm hoặc sửa file Markdown, build lại để đưa tài liệu vào image rồi chạy ingest:

```bash
docker compose up -d --build
docker compose exec telegram-bot python -m app.ingest
```

Lệnh ingest sẽ chia tài liệu thành các đoạn, tạo embedding bằng `nomic-embed-text`, rồi ghi đè collection `matcha_knowledge` trong Qdrant. Khi người dùng hỏi, bot tìm 4 đoạn liên quan nhất và gửi chúng cùng câu hỏi cho Qwen 7B.

## 7. Kiểm tra hoạt động

- Gửi `/start` → bot chào và giới thiệu.
- Gửi `/help` → bot hiện hướng dẫn.
- Gửi câu hỏi bất kỳ (vd: "Nhiệt độ nước pha matcha bao nhiêu?") → bot gọi Qwen qua Ollama và trả lời bằng LLM local.

## 8. Bước tiếp theo

- Thêm RAG: embedding bằng `bge-m3`/`multilingual-e5` và vector database Qdrant hoặc Chroma.
- Thêm Redis để lưu session/ngữ cảnh hội thoại nhiều lượt.
- Thêm CI/CD (Woodpecker/GitHub Actions) để tự động build & deploy khi push code.

## 9. Deploy lên VPS free (khuyến nghị nếu mạng local chặn Telegram)

> **Vì sao cần bước này**: một số mạng công ty/tổ chức chặn hoặc soi (SSL-inspect) traffic tới `api.telegram.org`, khiến bot báo lỗi `CERTIFICATE_VERIFY_FAILED` dù code hoàn toàn đúng. Cách xử lý an toàn nhất là chạy bot trên một máy chủ không bị chặn, thay vì tắt xác thực SSL (không an toàn).

### 9.1. Tạo VPS miễn phí (Oracle Cloud Always Free Tier)

1. Đăng ký tài khoản tại [oracle.com/cloud/free](https://www.oracle.com/cloud/free/) (cần thẻ để xác minh nhưng gói Always Free không bị trừ tiền).
2. Vào **Compute → Instances → Create Instance**.
3. Chọn image **Ubuntu 22.04/24.04**, shape thuộc nhóm **Always Free** (VM.Standard.A1.Flex hoặc VM.Standard.E2.1.Micro).
4. Tải về SSH key được cấp (hoặc dùng key có sẵn của bạn), ghi nhớ **Public IP**.

### 9.2. Cài Docker trên VPS

SSH vào VPS rồi chạy:

```bash
ssh -i /path/to/key ubuntu@<PUBLIC_IP>

# Trên VPS:
sudo apt update && sudo apt install -y ca-certificates curl gnupg
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

### 9.3. Đưa code lên VPS

Từ máy dev (thư mục `bot/`):

```bash
rsync -avz --exclude '.venv' --exclude '__pycache__' \
  -e "ssh -i /path/to/key" \
  ./ ubuntu@<PUBLIC_IP>:~/matcha-bot/
```

(Nếu dùng Git: đơn giản hơn là `git clone` repo trực tiếp trên VPS, miễn là không commit file `.env`.)

### 9.4. Chạy bot trên VPS

```bash
ssh -i /path/to/key ubuntu@<PUBLIC_IP>
cd ~/matcha-bot
cp .env.example .env   # điền BOT_TOKEN
docker compose up -d --build
docker compose logs -f
```

Vì Oracle Cloud không nằm sau proxy chặn Telegram, bot sẽ kết nối bình thường. Gửi `/start` trong Telegram để xác nhận.

### 9.5. Lưu ý bảo mật

- Không mở port nào ra ngoài internet cho bot này (polling mode không cần inbound port, chỉ cần outbound HTTPS).
- Trong Oracle Cloud, mặc định Security List đã chặn hết inbound trừ SSH (22) — không cần mở thêm port cho bot polling.
- Giữ file `.env` (chứa `BOT_TOKEN`) ngoài git, đã có `.gitignore` xử lý sẵn.

