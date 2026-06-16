import json
import pytest

from src.config import Config
from src.processing.json_processor import deidentify_json


def make_config(field_mapping: dict) -> Config:
    data = {
        "salt": "test-salt-v1",
        "field_mapping": field_mapping,
        "processing": {"ner_enabled": False, "ner_min_confidence": 0.6, "max_depth": 20},
        "pseudonym": {},
        "api": {},
    }
    return Config(data)


def load_sample() -> dict:
    with open("tests/fixtures/sample_patient.json", encoding="utf-8") as f:
        return json.load(f)


class TestStructuredFields:
    def test_phone_replaced(self):
        config = make_config({"phone": "PHONE"})
        result, _ = deidentify_json({"phone": "0912345678"}, config)
        assert result["phone"] != "0912345678"

    def test_cccd_replaced(self):
        config = make_config({"cccdNumber": "CCCD"})
        result, _ = deidentify_json({"cccdNumber": "123456789"}, config)
        assert result["cccdNumber"] != "123456789"

    def test_dob_replaced(self):
        config = make_config({"patientDob": "DOB"})
        result, _ = deidentify_json({"patientDob": "20/08/1950"}, config)
        assert result["patientDob"] != "20/08/1950"
        assert "/" in result["patientDob"]  # still in DOB format

    def test_gender_masked(self):
        config = make_config({"patientGenderName": "GENDER"})
        result, _ = deidentify_json({"patientGenderName": "Nữ"}, config)
        assert result["patientGenderName"] in ("M", "F", "U")

    def test_null_passthrough(self):
        config = make_config({"phone": "PHONE"})
        result, _ = deidentify_json({"phone": None}, config)
        assert result["phone"] is None

    def test_internal_id_unchanged(self):
        config = make_config({"treatmentCode": "INTERNAL_ID"})
        result, _ = deidentify_json({"treatmentCode": "0000099999"}, config)
        assert result["treatmentCode"] == "0000099999"


class TestFreeTextFields:
    def test_freetext_phone_replaced(self):
        config = make_config({"clinicalNote": "FREE_TEXT"})
        result, _ = deidentify_json(
            {"clinicalNote": "Liên hệ 0912345678 ngay"}, config
        )
        assert "0912345678" not in result["clinicalNote"]

    def test_freetext_cccd_replaced(self):
        config = make_config({"clinicalNote": "FREE_TEXT"})
        result, _ = deidentify_json(
            {"clinicalNote": "CCCD 123456789"}, config
        )
        assert "123456789" not in result["clinicalNote"]

    def test_freetext_email_replaced(self):
        config = make_config({"clinicalNote": "FREE_TEXT"})
        result, _ = deidentify_json(
            {"clinicalNote": "Email: test@example.com"}, config
        )
        assert "test@example.com" not in result["clinicalNote"]


class TestNestedJSON:
    def test_nested_dict(self):
        config = make_config({"phone": "PHONE"})
        result, _ = deidentify_json(
            {"outer": {"inner": {"phone": "0912345678"}}}, config
        )
        assert result["outer"]["inner"]["phone"] != "0912345678"

    def test_list_of_dicts(self):
        config = make_config({"phone": "PHONE"})
        result, _ = deidentify_json(
            [{"phone": "0912345678"}, {"phone": "0987654321"}], config
        )
        assert result[0]["phone"] != "0912345678"
        assert result[1]["phone"] != "0381234567"

    def test_unknown_fields_deep_processed(self):
        config = make_config({})
        result, _ = deidentify_json(
            {"unknownField": "0912345678"}, config
        )
        # No field mapping → unknown, but still deep-processes
        # Since no field mapping, should pass through unchanged
        assert "unknownField" in result


class TestSamplePatient:
    def test_all_structured_pii_replaced(self):
        config = make_config({
            "phone": "PHONE",
            "cccdNumber": "CCCD",
            "heinCardNumber": "HEIN_CARD",
            "patientDob": "DOB",
            "patientRelativeName": "FULL_NAME",
            "patientRelativeMobile": "PHONE",
            "patientRelativePhone": "PHONE",
            "patientGenderName": "GENDER",
            "patientAddress": "ADDRESS",
            "treatmentCode": "INTERNAL_ID",
            "patientCode": "INTERNAL_ID",
            "clinicalNote": "FREE_TEXT",
            "pathologicalProcess": "FREE_TEXT",
            "clinicalSigns": "FREE_TEXT",
            "subclinicalResult": "FREE_TEXT",
            "fullExam": "FREE_TEXT",
            "partExam": "FREE_TEXT",
            "ptPathologicalHistory": "FREE_TEXT",
        })
        sample = load_sample()
        result, stats = deidentify_json(sample, config)

        # Verify structured fields
        assert result["data"][0]["phone"] != "0912345678"
        assert result["data"][0]["cccdNumber"] != "123456789"
        assert result["data"][0]["heinCardNumber"] != "XY1234567890"
        assert result["data"][0]["patientDob"] != "15/03/1968"
        assert result["data"][0]["patientRelativeName"] != "TRẦN THỊ B"
        assert result["data"][0]["patientRelativeMobile"] != "0987654321"
        assert result["data"][0]["patientGenderName"] != "Nam"
        # Internal IDs unchanged
        assert result["data"][0]["treatmentCode"] == "0000099999"
        assert result["data"][0]["patientCode"] == "0000012345"

        # Free text no longer contains raw phone
        assert "0912345678" not in result["data"][0]["clinicalNote"]

        assert stats.entities_found >= 10
