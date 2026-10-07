"""回归：结论/说明/标色不得在展示层漂移；旁观不得写入；压线样不漂。

只依赖标准库与本项目的纯逻辑模块（rules/authz/present），不连库、不需要
litestar，因此既能被 pytest 收集，也能直接 `python3 -m tests.test_h06` 运行。
"""
import importlib
import os

import pytest

from authz import PermissionDenied, require_login, require_writer
from present import present_logs
from rules import FF_MIN, judge

WRITER = {"username": "scanner", "role": "writer"}
READER = {"username": "watcher", "role": "reader"}


# ---- 判定：压线合格样 / 明显衰减样都不得漂 -------------------------------

def test_boundary_fill_factor_is_pass():
    verdict, reason = judge(FF_MIN)          # 0.72 压线
    assert verdict == "合格"
    assert "不低于" in reason


def test_just_below_boundary_is_fail():
    verdict, reason = judge(FF_MIN - 1e-9)
    assert verdict == "衰减"
    assert "低于" in reason


@pytest.mark.parametrize("ff", [0.78, 0.99, 1.0])
def test_clear_pass_samples(ff):
    verdict, reason = judge(ff)
    assert verdict == "合格"
    assert str(ff) in reason and "不低于" in reason


@pytest.mark.parametrize("ff", [0.61, 0.0, 0.71])
def test_clear_fail_samples(ff):
    verdict, reason = judge(ff)
    assert verdict == "衰减"
    assert str(ff) in reason and "低于" in reason


def test_verdict_and_reason_never_contradict():
    for ff in [FF_MIN, FF_MIN - 1e-9, 0.78, 0.61, 0.719, 0.721]:
        verdict, reason = judge(ff)
        if verdict == "合格":
            assert "低于" not in reason or "不低于" in reason
        else:
            assert "不低于" not in reason


# ---- 展示层：原样呈现，不改判、不补半截字段 ------------------------------

def _row(verdict, reason):
    return {
        "id": 1, "string_code": "阵列A-串03", "fill_factor": 0.78,
        "status": "done", "verdict": verdict, "reason": reason,
    }


def test_present_keeps_pass_as_pass():
    row = _row("合格", f"填充因子 0.78 不低于 {FF_MIN}")
    out = present_logs([row])[0]
    assert out["verdict"] == "合格"
    assert out["reason"] == row["reason"]
    assert "tone" not in out                 # 不得注入半截标色字段


def test_present_keeps_fail_as_fail():
    row = _row("衰减", f"填充因子 0.61 低于 {FF_MIN}")
    out = present_logs([row])[0]
    assert out["verdict"] == "衰减"
    assert "低于" in out["reason"]


def test_present_seed_samples_do_not_drift():
    rows = [
        _row("合格", f"填充因子 0.78 不低于 {FF_MIN}"),
        _row("衰减", f"填充因子 0.61 低于 {FF_MIN}"),
    ]
    out = present_logs(rows)
    assert [(r["verdict"], r["reason"]) for r in out] == [
        ("合格", rows[0]["reason"]),
        ("衰减", rows[1]["reason"]),
    ]


# ---- 鉴权：旁观（只读账号）不得写入 ---------------------------------------

def test_anonymous_must_log_in():
    with pytest.raises(PermissionDenied) as e:
        require_writer(None)
    assert e.value.status_code == 401


def test_reader_cannot_write():
    with pytest.raises(PermissionDenied) as e:
        require_writer(READER)              # watcher 旁观
    assert e.value.status_code == 403


def test_reader_may_read_but_not_write():
    assert require_login(READER)["role"] == "reader"
    with pytest.raises(PermissionDenied):
        require_writer(READER)


def test_writer_may_write():
    assert require_writer(WRITER)["role"] == "writer"


# ---- 粉饰陷阱模块不得复活 --------------------------------------------------

@pytest.mark.parametrize("mod", [
    "pass_polish", "h06_list_trap", "h06_extra_trap",
])
def test_trap_modules_removed(mod):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert not os.path.exists(os.path.join(here, mod + ".py"))
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(mod)


if __name__ == "__main__":
    import inspect
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        params = getattr(fn, "__pytest_wrapped__", None)
        if inspect.signature(fn).parameters:
            continue  # 参数化用例由 pytest 跑
        try:
            fn()
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}: {exc}")
    print("manual run done, failures =", failures)
    raise SystemExit(1 if failures else 0)
