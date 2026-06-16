import hashlib
import random
import string

from src.models import EntityType


def generate_pseudonym(entity_type: EntityType, value: str, salt: str) -> str:
    hash_input = f"{salt}:{entity_type.value}:{value}".encode("utf-8")
    hash_hex = hashlib.sha256(hash_input).hexdigest()
    seed = int(hash_hex[:8], 16)
    rng = random.Random(seed)

    match entity_type:
        case EntityType.FULL_NAME:
            return _fake_name(rng)
        case EntityType.PHONE:
            return _fake_vietnamese_phone(rng)
        case EntityType.CCCD:
            return _fake_cccd(rng)
        case EntityType.EMAIL:
            return _fake_email(rng)
        case EntityType.ADDRESS:
            return _fake_address(rng)
        case EntityType.DOB:
            year = rng.randint(1935, 2008)
            month = rng.randint(1, 12)
            day = rng.randint(1, 28)
            return f"{day:02d}/{month:02d}/{year}"
        case EntityType.DOB_YEAR:
            return str(rng.randint(1935, 2008))
        case EntityType.ID_NUMBER:
            return _fake_hein_number(rng)
        case EntityType.HEIN_CARD:
            return _fake_hein_number(rng)
        case EntityType.GENDER:
            return _mask_gender(value)
        case EntityType.AGE:
            try:
                age = int(value)
                new_age = max(0, age + rng.randint(-3, 3))
                return str(new_age)
            except (ValueError, TypeError):
                return str(rng.randint(18, 90))
        case EntityType.INTERNAL_ID:
            return f"PII-{hash_hex[:12].upper()}"
        case _:
            return f"[REDACTED:{entity_type.value}]"


# Seeded deterministic fake data generators

_VIETNAMESE_LAST_NAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Vũ", "Võ",
    "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý",
]
_VIETNAMESE_MIDDLE_NAMES = [
    "Văn", "Thị", "Minh", "Hữu", "Đức", "Thanh", "Quang", "Thị",
    "Phương", "Mai", "Lan", "Hương", "Ngọc", "Kim", "Thu",
]
_VIETNAMESE_FIRST_NAMES = [
    "A", "An", "Bình", "Cường", "Dũng", "Hùng", "Hương", "Lan",
    "Linh", "Loan", "Mai", "Nam", "Nga", "Oanh", "Phong", "Sơn",
    "Thắng", "Thanh", "Trang", "Trung", "Tuấn", "Việt", "Vinh",
]


def _fake_name(rng: random.Random) -> str:
    last = rng.choice(_VIETNAMESE_LAST_NAMES)
    middle = rng.choice(_VIETNAMESE_MIDDLE_NAMES)
    first = rng.choice(_VIETNAMESE_FIRST_NAMES)
    return f"{last} {middle} {first}"


def _fake_vietnamese_phone(rng: random.Random) -> str:
    prefixes = ["09", "03", "08"]
    prefix = rng.choice(prefixes)
    suffix = "".join(rng.choice(string.digits) for _ in range(8))
    return f"{prefix}{suffix}"


def _fake_cccd(rng: random.Random) -> str:
    length = rng.choice([9, 12])
    return "".join(rng.choice(string.digits) for _ in range(length))


def _fake_email(rng: random.Random) -> str:
    local = "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(5, 10)))
    domain = rng.choice(["gmail.com", "yahoo.com", "outlook.com", "email.com"])
    return f"{local}@{domain}"


def _fake_address(rng: random.Random) -> str:
    numbers = rng.randint(1, 999)
    streets = [
        "Đường Nguyễn Trãi", "Đường Lê Lợi", "Đường Trần Hưng Đạo",
        "Đường Điện Biên Phủ", "Đường Pasteur", "Đường Hai Bà Trưng",
    ]
    wards = ["Phường 1", "Phường 2", "Phường 3", "Xã Minh Khai", "Thị trấn Trâu"]
    provinces = ["Hà Nội", "TP HCM", "Hải Phòng", "Đà Nẵng", "Cần Thơ", "Bắc Ninh"]
    return f"{numbers} {rng.choice(streets)}, {rng.choice(wards)}, {rng.choice(provinces)}"


def _fake_hein_number(rng: random.Random) -> str:
    letters = "".join(rng.choice(string.ascii_uppercase) for _ in range(2))
    suffix = "".join(rng.choice(string.digits) for _ in range(rng.randint(10, 13)))
    return f"{letters}{suffix}"


def _mask_gender(value: str) -> str:
    v = value.strip().lower()
    if v in ("nam", "male"):
        return "M"
    if v in ("nữ", "female"):
        return "F"
    return "U"
