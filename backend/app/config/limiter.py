# app/config/limiter.py
# Shared slowapi Limiter instance.
# Imported by both main.py (to attach to app.state) and routes.py (for @limit decorators).

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
