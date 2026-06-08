import pytest
from sqlalchemy.exc import IntegrityError

from todos_app.core.error_responses import (
	ValidationErrorDetail,
	database_http_exception,
	database_validation_error_detail,
	is_duplicate_user_violation,
)
from todos_app.core.http_errors import DATABASE_CONSTRAINT_VIOLATION, DUPLICATE_USER


pytestmark = pytest.mark.unit


def test_is_duplicate_user_violation_detects_email_constraint() -> None:
	exc = IntegrityError("", {}, Exception("UNIQUE constraint failed: users.email"))
	assert is_duplicate_user_violation(exc) is True


def test_is_duplicate_user_violation_detects_username_constraint() -> None:
	exc = IntegrityError("", {}, Exception("UNIQUE constraint failed: users.username"))
	assert is_duplicate_user_violation(exc) is True


def test_is_duplicate_user_violation_returns_false_for_other_constraints() -> None:
	exc = IntegrityError("", {}, Exception("FOREIGN KEY constraint failed"))
	assert is_duplicate_user_violation(exc) is False


def test_database_validation_error_detail_omits_cause_when_disabled() -> None:
	detail = database_validation_error_detail(
		msg=DUPLICATE_USER,
		error_type="database_integrity_error",
		cause="UNIQUE constraint failed: users.email",
		include_cause=False,
	)
	assert "ctx" not in detail[0]


def test_database_http_exception_includes_cause_when_enabled() -> None:
	exc = IntegrityError("", {}, Exception("UNIQUE constraint failed: users.email"))
	http_exc = database_http_exception(
		status_code=409,
		msg=DATABASE_CONSTRAINT_VIOLATION,
		error_type="database_integrity_error",
		exc=exc,
		include_cause=True,
	)
	detail = http_exc.detail
	assert isinstance(detail, list)
	parsed = ValidationErrorDetail.model_validate(detail[0])
	assert parsed.ctx is not None
	assert parsed.ctx["cause"] == "UNIQUE constraint failed: users.email"
