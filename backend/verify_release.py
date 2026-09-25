"""放行 / 未放行核对。

同一份核对覆盖四处真实数据链路：判定入口（rules.judge）、字段送审、
详情展示、列表展示——温度必须是录入的真实值，结论必须由真实规则得出。

运行：先启动 PostgreSQL，再用 DATABASE_URL 指向它，在 backend 目录下执行

    DATABASE_URL=postgresql://app:app@localhost:54393/herb python verify_release.py

（compose 环境的数据库正是该地址。脚本通过 FastAPI TestClient 在进程内
调接口，不额外占用 HTTP 端口。）
"""

import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rules import judge  # noqa: E402
import app as app_module  # noqa: E402


def fry(doc: dict) -> dict:
    return next(s for s in doc["steps"] if s["name"] == "清炒")


def check(label: str, cond: bool, detail="") -> None:
    if not cond:
        raise AssertionError(f"核对失败：{label} {detail}")
    print(f"  ✓ {label}")


def main() -> None:
    # —— 规则层直判：真实温度、真实时长 ——
    print("规则层：")
    check("105℃ / 9 分钟且饮片合法应放行",
          judge({"steps": [{"name": "清炒", "temp_c": 105, "minutes": 9}]})[0] == "放行")
    check("40℃ 低温应未放行（黄芩情形）",
          judge({"steps": [{"name": "清炒", "temp_c": 40, "minutes": 12}]})[0] == "未放行")
    check("200℃ 超温应未放行",
          judge({"steps": [{"name": "清炒", "temp_c": 200, "minutes": 12}]})[0] == "未放行")
    check("105℃ 但时长不足应未放行",
          judge({"steps": [{"name": "清炒", "temp_c": 105, "minutes": 2}]})[0] == "未放行")

    with TestClient(app_module.app) as client:
        token = client.post(
            "/api/auth/login", json={"username": "processor", "password": "herb123456"}
        ).json()["access_token"]
        reader = client.post(
            "/api/auth/login", json={"username": "checker", "password": "check123456"}
        ).json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        rh = {"Authorization": f"Bearer {reader}"}

        # —— 放行核对：105℃ / 9 分钟，饮片合法 ——
        print("放行链路（写入→详情→列表，均须真实温度）：")
        r = client.post("/api/batches", headers=h, json={
            "herb": "甘草",
            "steps": [{"name": "清炒", "temp_c": 105, "minutes": 9}],
        })
        check("写入返回 201", r.status_code == 201, r.text)
        created = r.json()
        bid = created["id"]
        check("写入即判放行，理由为符合炮制要求",
              created["verdict"] == "放行" and "符合" in created["reason"], created)
        check("回包含真实温度 105（字段送审未被压改）", fry(created["doc"])["temp_c"] == 105, created)

        r = client.get(f"/api/batches/{bid}", headers=h)
        check("详情返回 200", r.status_code == 200, r.text)
        detail = r.json()
        check("详情结论为放行", detail["verdict"] == "放行", detail)
        check("详情可见真实温度 105 ℃", fry(detail["doc"])["temp_c"] == 105, detail)

        r = client.get("/api/batches", headers=h)
        check("列表返回 200", r.status_code == 200, r.text)
        rows = r.json()
        row = next(x for x in rows if x["id"] == bid)
        check("列表结论为放行", row["verdict"] == "放行", row)
        check("列表可见真实温度 105 ℃", fry(row["doc"])["temp_c"] == 105, row)
        check("列表行不带旁路标记", "bypass" not in row, row)

        # —— 未放行核对：黄芩 40℃ 继续未放行，且温度仍可见 ——
        print("未放行链路（黄芩，详情与列表均须未放行且温度可见）：")
        hq = next(x for x in rows if x["herb"] == "黄芩")
        check("列表中黄芩为未放行", hq["verdict"] == "未放行", hq)
        check("列表中黄芩温度 40 ℃ 仍可见（未被置空）", fry(hq["doc"])["temp_c"] == 40, hq)

        r = client.get(f"/api/batches/{hq['id']}", headers=rh)
        check("只读账号可看详情 200", r.status_code == 200, r.text)
        hd = r.json()
        check("详情中黄芩为未放行", hd["verdict"] == "未放行", hd)
        check("详情中黄芩温度 40 ℃ 仍可见", fry(hd["doc"])["temp_c"] == 40, hd)

        # 种子甘草（120℃ / 12 分钟）仍放行
        seeded = next(x for x in rows if x["herb"] == "甘草" and x["id"] != bid)
        check("种子甘草 120℃ / 12 分钟为放行", seeded["verdict"] == "放行", seeded)

        # —— 权限：只读账号不得写入 ——
        r = client.post("/api/batches", headers=rh, json={
            "herb": "甘草",
            "steps": [{"name": "清炒", "temp_c": 105, "minutes": 9}],
        })
        check("checker 写入被拒（403）", r.status_code == 403, r.status_code)

    print("\n全部核对通过：放行与未放行均吃真实数。")


if __name__ == "__main__":
    main()
