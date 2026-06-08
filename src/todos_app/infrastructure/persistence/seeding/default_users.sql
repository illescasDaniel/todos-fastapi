-- Default records for the users table.
-- Dev password for all seeded users: changeme
-- UUID literals are 32-char hex (no hyphens) to match SQLAlchemy Uuid storage.
INSERT INTO users (id, email, username, first_name, last_name, hashed_password, is_active, role)
VALUES
	(
		'019e7000000070008000000000000001',
		'jane@example.com',
		'jane',
		'Jane',
		'Doe',
		'$argon2id$v=19$m=65536,t=3,p=4$WoKJpFgP8VjTNP3DRq/WzA$3S5JkNoVCawwLfXDwjH5mnLVFdiO0rs+m7N8/6GimdA',
		TRUE,
		'user'
	),
	(
		'019e7000000070008000000000000002',
		'admin@example.com',
		'admin',
		'Admin',
		'User',
		'$argon2id$v=19$m=65536,t=3,p=4$WoKJpFgP8VjTNP3DRq/WzA$3S5JkNoVCawwLfXDwjH5mnLVFdiO0rs+m7N8/6GimdA',
		TRUE,
		'admin'
	);
