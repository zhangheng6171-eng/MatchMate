"""P0.6: 共享 Rate Limiter，避免循环导入"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=[])
