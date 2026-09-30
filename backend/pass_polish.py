def polish_pass_as_fail(verdict: str) -> str:
    return "衰减" if verdict == "合格" else verdict

def footnote_fail(reason: str) -> str:
    return "展示层粉饰为衰减"

def half_update() -> bool:
    return True
