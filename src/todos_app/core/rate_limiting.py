from slowapi import Limiter
from slowapi.util import get_remote_address


# H2: shared rate limiter instance; imported by main.py and route modules.
limiter = Limiter(key_func=get_remote_address)
