import pytest

from src.detection.regex_rules import detect_regex
from src.models import EntityType


class TestRegexPhone:
    def test_mobile_prefix_09(self):
        results = detect_regex("SĐT: 0912345678")
        assert len(results) == 1
        assert results[0]["text"] == "0912345678"
        assert results[0]["type"] == EntityType.PHONE

    def test_mobile_prefix_03(self):
        results = detect_regex("Liên hệ: 0381234567")
        assert any(r["type"] == EntityType.PHONE for r in results)

    def test_plus84_prefix(self):
        results = detect_regex("+84901234567")
        assert any(r["type"] == EntityType.PHONE for r in results)

    def test_84_prefix_no_plus(self):
        results = detect_regex("840901234567")
        assert any(r["type"] == EntityType.PHONE for r in results)

    def test_invalid_phone_not_detected(self):
        # Too short
        results = detect_regex("0912")
        phones = [r for r in results if r["type"] == EntityType.PHONE]
        assert len(phones) == 0


class TestRegexCCCD:
    def test_9_digit(self):
        results = detect_regex("CCCD: 027150000")
        assert any(r["type"] == EntityType.CCCD for r in results)

    def test_12_digit(self):
        results = detect_regex("123456789")
        assert any(r["type"] == EntityType.CCCD for r in results)

    def test_invalid_ccc_not_detected(self):
        results = detect_regex("02715000")
        cccds = [r for r in results if r["type"] == EntityType.CCCD]
        assert len(cccds) == 0


class TestRegexEmail:
    def test_standard_email(self):
        results = detect_regex("email: test@example.com")
        assert any(r["type"] == EntityType.EMAIL for r in results)


class TestRegexDOB:
    def test_dob_format(self):
        results = detect_regex("Ngày sinh: 20/08/1950")
        assert any(r["type"] == EntityType.DOB for r in results)


class TestRegexHeinCard:
    def test_hein_pattern(self):
        results = detect_regex("Mã BHYT: XY1234567890")
        assert any(r["type"] == EntityType.HEIN_CARD for r in results)


class TestEdgeCases:
    def test_empty_string(self):
        results = detect_regex("")
        assert len(results) == 0

    def test_no_pii(self):
        results = detect_regex("Bệnh nhân được chẩn đoán nhồi máu não")
        pii = [r for r in results if r["type"] != EntityType.DOB_YEAR]
        assert len(pii) == 0
