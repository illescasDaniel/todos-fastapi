import pytest

from todos_app.auth.domain.authorization import ADMIN_ROLE, AdminRequiredError, require_admin


pytestmark = pytest.mark.unit


def test_given_non_admin_role_when_requiring_admin_then_raises_admin_required() -> None:
	# given
	role = "user"

	# when
	with pytest.raises(AdminRequiredError):
		require_admin(role)

	# then


def test_given_admin_role_when_requiring_admin_then_succeeds() -> None:
	# given
	role = ADMIN_ROLE

	# when
	require_admin(role)

	# then
