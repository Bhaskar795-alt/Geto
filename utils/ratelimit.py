import time
from collections import defaultdict

_user_cmds = defaultdict(list)


def is_rate_limited(user_id: int, max_cmds: int = 5, window: int = 10) -> bool:
    now = time.time()
    _user_cmds[user_id] = [t for t in _user_cmds[user_id] if now - t < window]
    if len(_user_cmds[user_id]) >= max_cmds:
        return True
    _user_cmds[user_id].append(now)
    return False
