-- Default records for the todos table (owned by seeded user jane).
-- UUID literals are 32-char hex (no hyphens) to match SQLAlchemy Uuid storage.
INSERT INTO todos (id, title, description, priority, completed, owner_id)
VALUES
	(
		'019e7000000070008000000000000003',
		'Set up FastAPI project',
		'Initialize app, routes, and database wiring.',
		'high',
		TRUE,
		'019e7000000070008000000000000001'
	),
	(
		'019e7000000070008000000000000004',
		'Create first API endpoint',
		'Add a basic GET /todos endpoint and verify it works.',
		'medium',
		FALSE,
		'019e7000000070008000000000000001'
	),
	(
		'019e7000000070008000000000000005',
		'Write README usage notes',
		'Document install, run, and seed commands.',
		'low',
		FALSE,
		'019e7000000070008000000000000001'
	);
