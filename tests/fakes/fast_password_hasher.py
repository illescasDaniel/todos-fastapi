from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError


class FastPasswordHasher:
	"""Low-cost Argon2 for integration tests (not for production)."""

	def __init__(self) -> None:
		self._hasher = Argon2Hasher(time_cost=1, memory_cost=8, parallelism=1)

	def hash(self, plain_password: str) -> str:
		return self._hasher.hash(plain_password)

	def verify(self, plain_password: str, hashed_password: str) -> bool:
		try:
			self._hasher.verify(hashed_password, plain_password)
		except VerifyMismatchError:
			return False
		return True


_TEST_PASSWORD_HASHER = FastPasswordHasher()


def get_test_password_hasher() -> FastPasswordHasher:
	return _TEST_PASSWORD_HASHER
