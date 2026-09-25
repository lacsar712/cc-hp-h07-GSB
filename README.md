# 饮片炮制记录台

一条记录是一整包炮制文书，里面是工序数组，不是拆成多列指标的普通表单。清炒温度和时长不在范围内就不能放行。

## 端口

| 服务 | 地址 |
|------|------|
| 页面 | http://localhost:3193 |
| 接口 | http://localhost:8193 |
| PostgreSQL | localhost:54393 |

## 账号

| 用户 | 密码 | 权限 |
|------|------|------|
| processor | herb123456 | 可写 |
| checker | check123456 | 只读 |

## 启动

```bash
cd projects/14-herb-process-record
docker compose up --build
```

## 验收

1. processor 登录后，甘草为放行，黄芩为未放行（温度过低）。
2. 再写一条温度 200 的清炒，结论仍是未放行。
3. checker 看不到写入按钮。

## 核对

```bash
# 判定单测（放行 / 未放行各一组，无需数据库）
cd backend && python3 -m pytest test_rules.py -q

# 端到端核对（需先 docker compose up --build）
python3 scripts/verify_e2e.py
```

端到端核对覆盖：105℃/9min 放行且列表与详情都显示真实温度 105；黄芩继续未放行且温度不压空；200℃ 未放行；checker 写入被拒。
