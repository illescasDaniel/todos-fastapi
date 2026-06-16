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


def test_given_regular_user_actor_when_resolving_list_owner_filter_then_returns_actor_id() -> None:
	# given
	actor_id = TEST_ACTOR_ID
	actor_role = "user"

	# when
	result = list_owner_filter(actor_id=actor_id, actor_role=actor_role)

	# then
	assert result == TEST_ACTOR_ID


def test_given_admin_actor_when_resolving_list_owner_filter_then_returns_none() -> None:
	# given
	actor_id = TEST_ACTOR_ID
	actor_role = ADMIN_ROLE

	# when
	result = list_owner_filter(actor_id=actor_id, actor_role=actor_role)

	# then
	assert result is None


def test_given_regular_user_with_requested_owner_when_resolving_create_owner_id_then_ignores_request() -> None:
	# given
	actor_id = TEST_ACTOR_ID
	actor_role = "user"
	requested_owner_id = UNKNOWN_ID

	# when
	result = resolve_create_owner_id(
		actor_id=actor_id,
		actor_role=actor_role,
		requested_owner_id=requested_owner_id,
	)

	# then
	assert result == TEST_ACTOR_ID


def test_given_admin_with_requested_owner_when_resolving_create_owner_id_then_uses_requested() -> None:
	# given
	actor_id = TEST_USER_ID
	actor_role = ADMIN_ROLE
	requested_owner_id = TEST_USER_ID_B

	# when
	result = resolve_create_owner_id(
		actor_id=actor_id,
		actor_role=actor_role,
		requested_owner_id=requested_owner_id,
	)

	# then
	assert result == TEST_USER_ID_B


def test_given_admin_without_requested_owner_when_resolving_create_owner_id_then_defaults_to_actor() -> None:
	# given
	actor_id = TEST_USER_ID
	actor_role = ADMIN_ROLE

	# when
	result = resolve_create_owner_id(
		actor_id=actor_id,
		actor_role=actor_role,
		requested_owner_id=None,
	)

	# then
	assert result == TEST_USER_ID


def test_given_regular_user_changing_todo_owner_when_checking_owner_change_forbidden_then_returns_true() -> None:
	# given
	actor_role = "user"
	existing_owner_id = TEST_USER_ID
	requested_owner_id = TEST_USER_ID_B

	# when
	result = is_update_owner_change_forbidden(
		actor_role=actor_role,
		existing_owner_id=existing_owner_id,
		requested_owner_id=requested_owner_id,
	)

	# then
	assert result is True


def test_given_admin_changing_todo_owner_when_checking_owner_change_forbidden_then_returns_false() -> None:
	# given
	actor_role = ADMIN_ROLE
	existing_owner_id = TEST_USER_ID
	requested_owner_id = TEST_USER_ID_B

	# when
	result = is_update_owner_change_forbidden(
		actor_role=actor_role,
		existing_owner_id=existing_owner_id,
		requested_owner_id=requested_owner_id,
	)

	# then
	assert result is False


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
