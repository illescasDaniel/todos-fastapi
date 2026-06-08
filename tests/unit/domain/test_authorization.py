import pytest

from factories import TEST_ACTOR_ID, TEST_USER_ID, TEST_USER_ID_B
from todos_app.domain.auth.authorization import (
	ADMIN_ROLE,
	AdminRequiredError,
	is_update_owner_change_forbidden,
	list_owner_filter,
	require_admin,
	resolve_create_owner_id,
)
from todos_app.domain.ids import UNKNOWN_ID


pytestmark = pytest.mark.unit


def test_list_owner_filter_regular_user() -> None:
	assert list_owner_filter(actor_id=TEST_ACTOR_ID, actor_role="user") == TEST_ACTOR_ID


def test_list_owner_filter_admin() -> None:
	assert list_owner_filter(actor_id=TEST_ACTOR_ID, actor_role=ADMIN_ROLE) is None


def test_resolve_create_owner_id_regular_user_ignores_requested() -> None:
	assert (
		resolve_create_owner_id(actor_id=TEST_ACTOR_ID, actor_role="user", requested_owner_id=UNKNOWN_ID)
		== TEST_ACTOR_ID
	)


def test_resolve_create_owner_id_admin_uses_requested() -> None:
	assert (
		resolve_create_owner_id(actor_id=TEST_USER_ID, actor_role=ADMIN_ROLE, requested_owner_id=TEST_USER_ID_B)
		== TEST_USER_ID_B
	)


def test_resolve_create_owner_id_admin_defaults_to_actor() -> None:
	assert (
		resolve_create_owner_id(actor_id=TEST_USER_ID, actor_role=ADMIN_ROLE, requested_owner_id=None) == TEST_USER_ID
	)


def test_is_update_owner_change_forbidden_for_regular_user() -> None:
	assert is_update_owner_change_forbidden(
		actor_role="user",
		existing_owner_id=TEST_USER_ID,
		requested_owner_id=TEST_USER_ID_B,
	)


def test_is_update_owner_change_forbidden_admin_may_reassign() -> None:
	assert not is_update_owner_change_forbidden(
		actor_role=ADMIN_ROLE,
		existing_owner_id=TEST_USER_ID,
		requested_owner_id=TEST_USER_ID_B,
	)


def test_require_admin_raises_for_non_admin() -> None:
	with pytest.raises(AdminRequiredError):
		require_admin("user")


def test_require_admin_allows_admin() -> None:
	require_admin(ADMIN_ROLE)
