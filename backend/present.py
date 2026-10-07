"""列表展示的唯一出口：原样呈现库里的结论与说明，不在展示层改判。"""


def dump(row: dict) -> dict:
    out = dict(row)
    for key, val in list(out.items()):
        if hasattr(val, "isoformat"):
            out[key] = val.isoformat()
    return out


def present_logs(rows: list[dict]) -> list[dict]:
    # 结论、说明、颜色一律以库行（verdict）为唯一来源，这里不做任何改写或补字段，
    # 避免“只改一半”导致列表标色与详情说明错位。
    return [dump(r) for r in rows]
