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


def test_given_email_unique_violation_when_checking_duplicate_user_then_returns_true() -> None:
	# given
	exc = IntegrityError("", {}, Exception("UNIQUE constraint failed: users.email"))

	# when
	result = is_duplicate_user_violation(exc)

	# then
	assert result is True


def test_given_username_unique_violation_when_checking_duplicate_user_then_returns_true() -> None:
	# given
	exc = IntegrityError("", {}, Exception("UNIQUE constraint failed: users.username"))

	# when
	result = is_duplicate_user_violation(exc)

	# then
	assert result is True


def test_given_foreign_key_violation_when_checking_duplicate_user_then_returns_false() -> None:
	# given
	exc = IntegrityError("", {}, Exception("FOREIGN KEY constraint failed"))

	# when
	result = is_duplicate_user_violation(exc)

	# then
	assert result is False


def test_given_cause_disabled_when_building_validation_detail_then_omits_context() -> None:
	# given
	cause = "UNIQUE constraint failed: users.email"

	# when
	detail = database_validation_error_detail(
		msg=DUPLICATE_USER,
		error_type="database_integrity_error",
		cause=cause,
		include_cause=False,
	)

	# then
	assert "ctx" not in detail[0]


def test_given_cause_enabled_when_building_database_http_exception_then_includes_cause() -> None:
	# given
	exc = IntegrityError("", {}, Exception("UNIQUE constraint failed: users.email"))

	# when
	http_exc = database_http_exception(
		status_code=409,
		msg=DATABASE_CONSTRAINT_VIOLATION,
		error_type="database_integrity_error",
		exc=exc,
		include_cause=True,
	)

	# then
	detail = http_exc.detail
	assert isinstance(detail, list)
	parsed = ValidationErrorDetail.model_validate(detail[0])
	assert parsed.ctx is not None
	assert parsed.ctx["cause"] == "UNIQUE constraint failed: users.email"
