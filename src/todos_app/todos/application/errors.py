class TodoNotFoundError(Exception):
	def __init__(self, *, actor_role: str) -> None:
		self.actor_role = actor_role
		super().__init__()


class TodoOwnerChangeForbiddenError(Exception):
	pass
