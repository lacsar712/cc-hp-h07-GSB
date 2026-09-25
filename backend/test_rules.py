"""判定核对：放行与未放行各一组，均吃真实温度时长。"""

from rules import judge


def doc(temp_c, minutes, name="清炒"):
    return {"steps": [{"name": name, "temp_c": temp_c, "minutes": minutes}]}


# ---- 放行核对 ----

def test_release_105c_9min():
    verdict, reason = judge(doc(105, 9))
    assert verdict == "放行"
    assert reason == "清炒工序符合炮制要求"


def test_release_boundaries():
    assert judge(doc(80, 5))[0] == "放行"
    assert judge(doc(150, 30))[0] == "放行"


# ---- 未放行核对 ----

def test_hold_huangqin_40c():
    verdict, reason = judge(doc(40, 12))
    assert verdict == "未放行"
    assert reason == "清炒温度不在范围内"


def test_hold_200c():
    verdict, reason = judge(doc(200, 10))
    assert verdict == "未放行"
    assert reason == "清炒温度不在范围内"


def test_hold_minutes_out_of_range():
    verdict, reason = judge(doc(120, 60))
    assert verdict == "未放行"
    assert reason == "清炒时长不在范围内"


def test_hold_missing_fry_step():
    verdict, reason = judge({"steps": [{"name": "润制", "temp_c": 50, "minutes": 30}]})
    assert verdict == "未放行"
    assert reason == "缺少清炒工序"
