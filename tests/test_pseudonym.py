import pytest

from src.models import EntityType
from src.pseudonym.mapper import _mapping_cache, get_pseudonym
from src.pseudonym.generator import generate_pseudonym


@pytest.fixture(autouse=True)
def clear_cache():
    _mapping_cache.clear()


class TestDeterminism:
    def test_same_input_same_output(self):
        """Same (type, value, salt) must produce identical pseudonym."""
        salt = "test-salt-v1"
        phone = "0912345678"

        result1 = get_pseudonym(EntityType.PHONE, phone, salt)
        result2 = get_pseudonym(EntityType.PHONE, phone, salt)
        assert result1 == result2

    def test_different_salt_different_output(self):
        """Different salt → different pseudonym."""
        phone = "0912345678"
        p1 = get_pseudonym(EntityType.PHONE, phone, "salt-v1")
        p2 = get_pseudonym(EntityType.PHONE, phone, "salt-v2")
        assert p1 != p2

    def test_same_person_two_fields_same_pseudonym(self):
        """If patientRelativeName == patientMotherName, both get same pseudonym."""
        salt = "test-salt"
        name = "NGUYỄN VĂN A"
        p1 = get_pseudonym(EntityType.FULL_NAME, name, salt)
        p2 = get_pseudonym(EntityType.FULL_NAME, name, salt)
        assert p1 == p2


class TestFakerOutputFormat:
    def test_phone_prefix_valid(self):
        salt = "test"
        for _ in range(10):
            phone = generate_pseudonym(EntityType.PHONE, "0912345678", salt)
            assert phone.startswith(("09", "03", "08"))
            assert len(phone) == 10

    def test_cccd_length(self):
        salt = "test"
        cccd = generate_pseudonym(EntityType.CCCD, "123456789", salt)
        assert len(cccd) in (9, 12)

    def test_gender_masked(self):
        assert generate_pseudonym(EntityType.GENDER, "Nam", "s") in ("M", "F", "U")
        assert generate_pseudonym(EntityType.GENDER, "Nữ", "s") in ("M", "F", "U")


class TestFallback:
    def test_unknown_entity_type(self):
        """Unknown entity type → fallback [REDACTED:TYPE]."""
        result = generate_pseudonym(EntityType.BLOOD_TYPE, "A", "s")
        assert result == "[REDACTED:BLOOD_TYPE]"


class TestCache:
    def test_cache_hit_returns_same(self):
        salt = "test"
        _mapping_cache.clear()
        v = "0912345678"
        p1 = get_pseudonym(EntityType.PHONE, v, salt)
        p2 = get_pseudonym(EntityType.PHONE, v, salt)
        assert p1 == p2
