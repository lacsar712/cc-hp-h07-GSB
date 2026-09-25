#!/usr/bin/env python3
"""端到端核对：放行与未放行各一组，判定、详情、列表都验真实温度。

用法：先 docker compose up --build，再 python3 scripts/verify_e2e.py
可用 BASE_URL 环境变量覆盖接口地址（默认 http://localhost:8193）。
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("BASE_URL", "http://localhost:8193")

failures = []


def check(label, ok, extra=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"  ({extra})" if extra else ""))
    if not ok:
        failures.append(label)


def api(path, token=None, method="GET", body=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")


def login(username, password):
    status, data = api("/api/auth/login", method="POST", body={"username": username, "password": password})
    assert status == 200, f"登录失败 {username}: {status} {data}"
    return data["access_token"]


def fry_step(row):
    return next(s for s in row["doc"]["steps"] if s["name"] == "清炒")


def main():
    token = login("processor", "herb123456")

    # ---- 放行核对：105℃ 9 分钟、饮片合法，应放行，详情与列表都看得见 105 ----
    status, created = api("/api/batches", token, "POST",
                          {"herb": "白芍", "steps": [{"name": "清炒", "temp_c": 105, "minutes": 9}]})
    check("写入 105℃/9min 返回 201", status == 201, f"got {status}")
    check("105℃/9min 判定为放行", created.get("verdict") == "放行", created.get("verdict"))
    new_id = created["id"]

    status, rows = api("/api/batches", token)
    row = next((r for r in rows if r["id"] == new_id), None)
    check("列表含新记录", row is not None)
    if row:
        temp = fry_step(row)["temp_c"]
        check("列表温度为真实值 105", temp == 105, f"got {temp!r}")

    status, detail = api(f"/api/batches/{new_id}", token)
    step = fry_step(detail)
    check("详情温度为真实值 105", step["temp_c"] == 105, f"got {step['temp_c']!r}")
    check("详情时长为真实值 9", step["minutes"] == 9, f"got {step['minutes']!r}")
    check("详情结论为放行", detail.get("verdict") == "放行", detail.get("verdict"))

    # ---- 未放行核对：黄芩温度过低继续未放行，温度不压空 ----
    huangqin = next((r for r in rows if r["herb"] == "黄芩"), None)
    check("列表含黄芩", huangqin is not None)
    if huangqin:
        check("黄芩继续未放行", huangqin["verdict"] == "未放行", huangqin["verdict"])
        temp = fry_step(huangqin)["temp_c"]
        check("黄芩列表温度为真实值 40", temp == 40, f"got {temp!r}")
        status, hq_detail = api(f"/api/batches/{huangqin['id']}", token)
        check("黄芩详情温度为真实值 40", fry_step(hq_detail)["temp_c"] == 40)

    status, hot = api("/api/batches", token, "POST",
                      {"herb": "白芍", "steps": [{"name": "清炒", "temp_c": 200, "minutes": 10}]})
    check("200℃ 记录仍为未放行", hot.get("verdict") == "未放行", hot.get("verdict"))

    # ---- 权限核对：checker 只读 ----
    checker = login("checker", "check123456")
    status, _ = api("/api/batches", checker, "POST",
                    {"herb": "白芍", "steps": [{"name": "清炒", "temp_c": 105, "minutes": 9}]})
    check("checker 写入被拒 403", status == 403, f"got {status}")

    print()
    if failures:
        print(f"{len(failures)} 项未通过")
        return 1
    print("全部核对通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
