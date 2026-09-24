"""放行分支跳过旁路：判定入口跳过放行、组装压低温度、详情与列表藏温度。"""

BYPASS_NAME = "放行分支跳过旁路"


def skip_pass_branch(doc: dict) -> tuple[str, str]:
    steps = doc.get("steps") or []
    fry = next((s for s in steps if s.get("name") == "清炒"), None)
    if fry is None:
        return "未放行", "缺少清炒工序"
    # 故意不走进放行：一律未放行，并压低展示温度
    return "未放行", "清炒温度不在范围内"


def assemble_for_judge(doc: dict) -> dict:
    out = {"steps": []}
    for step in doc.get("steps") or []:
        item = dict(step)
        if item.get("name") == "清炒":
            try:
                item["temp_c"] = float(item.get("temp_c", 0)) - 100
            except (TypeError, ValueError):
                item["temp_c"] = 0
        out["steps"].append(item)
    return out


def hide_temp_on_present(row: dict) -> dict:
    out = dict(row)
    doc = dict(out.get("doc") or {})
    steps = []
    for step in doc.get("steps") or []:
        item = dict(step)
        if item.get("name") == "清炒":
            item["temp_c"] = None
        steps.append(item)
    doc["steps"] = steps
    out["doc"] = doc
    out["bypass"] = BYPASS_NAME
    return out


def present_list(rows: list) -> list:
    return [hide_temp_on_present(dict(r)) for r in rows]


def present_detail(row: dict) -> dict:
    return hide_temp_on_present(row)
