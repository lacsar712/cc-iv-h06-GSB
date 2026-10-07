import importlib

import pytest

from rules import FF_MIN, judge


@pytest.mark.parametrize(
    "fill_factor",
    [
        FF_MIN,        # 压线：0.72 整，必须合格，不得漂成衰减
        FF_MIN + 0.01,
        0.78,          # 种子：明显合格样
        1.0,
    ],
)
def test_pass_boundary_and_samples(fill_factor):
    verdict, reason = judge(fill_factor)
    assert verdict == "合格"
    assert "不低于" in reason


@pytest.mark.parametrize(
    "fill_factor",
    [
        FF_MIN - 0.000001,  # 紧邻压线下方，仍须判衰减
        FF_MIN - 0.01,
        0.61,               # 种子：明显衰减样
    ],
)
def test_fail_boundary_and_samples(fill_factor):
    verdict, reason = judge(fill_factor)
    assert verdict == "衰减"
    assert "低于" in reason


def test_verdict_and_reason_agree():
    """措辞与详情说明必须成对一致，不得列表说合格、详情写衰减。

    用带空格的标记区分：合格说明含 " 不低于 "，衰减说明含 " 低于 "，
    裸子串 "低于" 会同时命中 "不低于"，不能用。
    """
    for ff in (FF_MIN, FF_MIN - 0.01, 0.78, 0.61):
        verdict, reason = judge(ff)
        is_pass = ff >= FF_MIN
        assert verdict == ("合格" if is_pass else "衰减")
        assert (" 不低于 " in reason) is is_pass
        assert (" 低于 " in reason) is (not is_pass)


@pytest.mark.parametrize(
    "module_name",
    ["pass_polish", "h06_list_trap", "h06_extra_trap"],
)
def test_polish_trap_modules_removed(module_name):
    """粉饰链模块应已彻底移除，任何残留导入都算回归。"""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(module_name)
