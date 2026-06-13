import warnings

from slowapi import Limiter
from slowapi.util import get_remote_address


# slowapi 0.1.10 still calls asyncio.iscoroutinefunction (laurentS/slowapi#263).
# Drop this once a PyPI release switches to inspect.iscoroutinefunction.
warnings.filterwarnings(
	"ignore",
	message="'asyncio.iscoroutinefunction' is deprecated.*",
	category=DeprecationWarning,
	module="slowapi.extension",
)


# H2: shared rate limiter instance; imported by main.py and route modules.
limiter = Limiter(key_func=get_remote_address)
