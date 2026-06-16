from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError

from env_config.schema import EnvSettings


class Argon2PasswordHasher:
	def __init__(self, settings: EnvSettings) -> None:
		self._hasher = Argon2Hasher(
			time_cost=settings.argon2.time_cost,
			memory_cost=settings.argon2.memory_cost,
			parallelism=settings.argon2.parallelism,
		)

	def hash(self, plain_password: str) -> str:
		return self._hasher.hash(plain_password)

	def verify(self, plain_password: str, hashed_password: str) -> bool:
		try:
			self._hasher.verify(hashed_password, plain_password)
		except VerifyMismatchError:
			return False
		return True
