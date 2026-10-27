"""Conservative header-only sensitive-information hints (no row inspection)."""
from __future__ import annotations
from typing import Iterable

_HINTS = {
    "contact": ("이메일", "전화번호", "휴대폰", "휴대전화", "연락처",
                "email", "e-mail", "phone", "mobile_number"),
    "identity": ("주민등록", "주민번호", "여권번호", "passport", "social_security",
                 "socialsecurity", "ssn", "고객명", "성명", "full_name",
                 "first_name", "last_name", "생년월일", "birth_date"),
    "location": ("주소", "우편번호", "address", "postal_code", "zip_code"),
    "financial": ("계좌번호", "계좌", "카드번호", "bank_account", "card_number"),
}


def inspect_header_privacy(columns: Iterable[str]) -> dict:
    """Return only aggregate header hints; zero hits cannot clear user data."""
    matched, categories = 0, set()
    for column in columns:
        name = str(column).casefold()
        types = {kind for kind, words in _HINTS.items()
                 if any(word in name for word in words)}
        if types:
            matched += 1
            categories.update(types)
    return {
        "version": "header-hints-v1",
        "checked": "column_names_only",
        "suspected_column_count": matched,
        "hint_categories": sorted(categories),
        "source_values_inspected": False,
        "automatic_privacy_clearance": False,
        "manual_deidentification_review_required": True,
    }


def privacy_header_notice(review: dict) -> str:
    count = review["suspected_column_count"]
    if count:
        return (
            f"개인정보 주의: 열 이름에서 민감정보 의심 열 {count}개를 탐지했습니다. "
            "원본 값은 검사하지 않았으며 별도 비식별화 검수가 필요합니다."
        )
    return (
        "개인정보 주의: 열 이름에서 단서가 없더라도 원본 값의 "
        "민감정보 부재가 검증된 것은 아닙니다. 별도 검수가 필요합니다."
    )
