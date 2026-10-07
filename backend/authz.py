"""只读的鉴权判定。纯标准库、不连库，便于单测锁死“旁观不得写入”。"""

WRITER = "writer"
READER = "reader"


class PermissionDenied(Exception):
    def __init__(self, detail: str, status_code: int):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def require_login(user: dict | None) -> dict:
    if user is None:
        raise PermissionDenied("未登录", 401)
    return user


def require_writer(user: dict | None) -> dict:
    require_login(user)
    if user.get("role") != WRITER:
        raise PermissionDenied("仅扫描员可提交IV扫描", 403)
    return user
