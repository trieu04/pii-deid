# PII De-identification Service

Loại bỏ thông tin cá nhân (PII) khỏi hồ sơ bệnh nhân, thay thế bằng định danh giả nội bộ nhất quán.

## Tính năng

- **Detection**: Regex rules cho phone, CCCD, email, DOB, thẻ BHYT + Underthesea NER cho tiếng Việt
- **Deterministic pseudonymization**: Cùng giá trị PII → cùng pseudonym (hash-based, salt-keyed)
- **JSON processing**: Recursive walk, xử lý nested objects và arrays
- **2 chế độ**: Direct (nhận JSON đã fetch) và Proxy (fetch upstream rồi de-id)
- **Config-driven**: Tất cả field mapping, patterns trong `config.yaml`
- **No external DB**: In-memory LRU cache cho pseudonym mapping

## API Endpoints

### POST /api/v1/deidentify

Direct mode — gửi JSON đã fetch lên de-identify.

```bash
curl -X POST http://localhost:8000/api/v1/deidentify \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "phone": "0912345678",
      "patientDob": "15/03/1968",
      "cccdNumber": "123456789"
    }
  }'
```

Response:
```json
{
  "success": true,
  "data": { "phone": "0901234567", "patientDob": "15/03/1968", "cccdNumber": "123456789" },
  "meta": { "entities_found": 3, "processing_ms": 12.5 }
}
```

### POST /api/v1/deidentify/proxy

Proxy mode — chuyển tiếp request đến upstream (bệnh viện), nhận response, de-identify, trả về.

```bash
curl -X POST http://localhost:8000/api/v1/deidentify/proxy \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_UPSTREAM_API_KEY" \
  -d '{"treatmentCodes": ["0000099999"]}'
```

### GET /health

Health check — `{status: "ok", version: "1.0.0"}`

### GET /api/v1/deidentify/stats

Cache statistics — `{cache_size: 142}`

## Quick Start

### Docker

```bash
cp config.yaml config.yaml.local
# Chỉnh PII_SALT trong config.yaml.local
X_API_KEY=your_key docker compose up -d
```

### Local

```bash
pip install -r requirements.txt
cp config.yaml config.yaml
# Chỉnh PII_SALT trong config.yaml
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Configuration

| Key | Mô tả |
|-----|--------|
| `salt` | Salt cho deterministic hash — đổi annually để regenerate pseudonym space |
| `field_mapping` | Map field name → entity type |
| `processing.ner_enabled` | Bật/tắt Underthesea NER cho free-text fields |
| `api.upstream_url` | URL upstream khi dùng proxy mode |
| `X_API_KEY` env var | API key cho upstream (dùng trong proxy mode) |

## PII Entity Types

| Type | Detection | Replacement |
|------|-----------|-------------|
| `FULL_NAME` | NER + structured field | Faker VN name |
| `PHONE` | Regex | Fake VN phone (09x/03x/08x) |
| `CCCD` | Regex (9 hoặc 12 số) | Fake CCCD pattern |
| `EMAIL` | Regex | Fake email |
| `ADDRESS` | NER + structured field | Fake VN address |
| `DOB` | Regex (DD/MM/YYYY) | Fake DOB |
| `HEIN_CARD` | Regex | Fake ID pattern |
| `GENDER` | Structured field | Masked (M/F) |
| `INTERNAL_ID` | Structured field | Giữ nguyên |
| `FREE_TEXT` | Regex + NER | Replace từng PII found |

## Testing

```bash
pytest tests/ -v
```

## Architecture

```
Request (JSON hoặc proxy)
    ↓
deidentify_json() — recursive walk
    ↓
_field có mapping_ → get_pseudonym() → LRU cache → seeded RNG → fake data
_field = FREE_TEXT_ → detect_all() → regex + NER → replace từng entity
    ↓
Response (de-identified JSON)
```

## Deployment Notes

- Salt nên đặt qua env var, không commit vào git
- Thay đổi salt → tất cả pseudonym thay đổi (consistent re-generation)
- Cache LRU max 50,000 entries — restart server để clear nếu cần
