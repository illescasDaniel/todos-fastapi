import logging
import sys


logger = logging.getLogger("todos_app")


def configure_logger() -> None:
	if logger.handlers:
		return

	logger.setLevel(logging.INFO)
	formatter = logging.Formatter(
		"%(asctime)s | %(levelname)s | %(name)s | %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)

	stream_handler = logging.StreamHandler(sys.stdout)
	stream_handler.setFormatter(formatter)

	file_handler = logging.FileHandler("todos_app.log", encoding="utf-8")
	file_handler.setFormatter(formatter)

	logger.addHandler(stream_handler)
	logger.addHandler(file_handler)
	logger.propagate = False
