import math
import json
from datetime import datetime

def calculate(expression):
    try:
        allowed = set('0123456789+-*/().% ')
        safe_expr = expression.replace('**', '^')
        result = eval(expression, {"__builtins__": {}}, {
            "math": math, "sqrt": math.sqrt, "sin": math.sin,
            "cos": math.cos, "tan": math.tan, "log": math.log,
            "pi": math.pi, "e": math.e, "abs": abs, "round": round
        })
        return result
    except Exception as ex:
        return f"錯誤: {ex}"

calculations = [
    ("基本加法", "123 + 456"),
    ("基本減法", "1000 - 375"),
    ("基本乘法", "48 * 25"),
    ("基本除法", "9999 / 7"),
    ("次方運算", "2 ** 10"),
    ("取餘數", "100 % 7"),
    ("複雜運算", "(150 + 250) * 3 / 4 - 50"),
    ("平方根", "sqrt(144)"),
    ("圓周率", "round(pi * 10 ** 2, 4)"),
    ("自然對數", "round(log(math.e ** 5), 6)"),
    ("三角函數 sin", "round(sin(pi / 2), 6)"),
    ("三角函數 cos", "round(cos(0), 6)"),
    ("絕對值", "abs(-999)"),
    ("四捨五入", "round(3.14159265, 3)"),
    ("複合計算", "sqrt(3**2 + 4**2)"),
]

results = []
for name, expr in calculations:
    val = calculate(expr)
    results.append({"name": name, "expression": expr, "result": val})

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python 計算機系統</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 40px 20px;
            color: #e0e0e0;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .header h1 {{
            font-size: 2.5rem;
            background: linear-gradient(90deg, #00d4ff, #7b2ff7, #00d4ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }}
        .header p {{
            color: #88aacc;
            font-size: 0.95rem;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(0,212,255,0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
        }}
        .stat-card .value {{
            font-size: 2rem;
            font-weight: 700;
            color: #00d4ff;
        }}
        .stat-card .label {{
            font-size: 0.85rem;
            color: #88aacc;
            margin-top: 4px;
        }}
        .table-wrapper {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(0,212,255,0.15);
            border-radius: 16px;
            overflow: hidden;
            backdrop-filter: blur(10px);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        thead {{
            background: linear-gradient(90deg, rgba(0,212,255,0.15), rgba(123,47,247,0.15));
        }}
        th {{
            padding: 16px 20px;
            text-align: left;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #00d4ff;
            border-bottom: 1px solid rgba(0,212,255,0.2);
        }}
        td {{
            padding: 14px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 0.95rem;
        }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover td {{ background: rgba(0,212,255,0.05); }}
        .tag {{
            display: inline-block;
            background: rgba(123,47,247,0.25);
            border: 1px solid rgba(123,47,247,0.4);
            color: #c4a0ff;
            border-radius: 6px;
            padding: 3px 10px;
            font-size: 0.82rem;
        }}
        .expr {{
            font-family: 'Consolas', 'Courier New', monospace;
            color: #88ccff;
            background: rgba(0,0,0,0.25);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.9rem;
        }}
        .result {{
            font-weight: 700;
            font-size: 1.05rem;
            color: #00ffaa;
            font-family: 'Consolas', monospace;
        }}
        .footer {{
            text-align: center;
            margin-top: 32px;
            color: #446688;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Python 計算機系統</h1>
            <p>執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="value">{len(results)}</div>
                <div class="label">總計算數</div>
            </div>
            <div class="stat-card">
                <div class="value">{sum(1 for r in results if not str(r['result']).startswith('錯誤'))}</div>
                <div class="label">成功計算</div>
            </div>
            <div class="stat-card">
                <div class="value">{sum(1 for r in results if str(r['result']).startswith('錯誤'))}</div>
                <div class="label">錯誤計算</div>
            </div>
        </div>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>運算類型</th>
                        <th>表達式</th>
                        <th>計算結果</th>
                    </tr>
                </thead>
                <tbody>
"""

for i, r in enumerate(results, 1):
    html += f"""                    <tr>
                        <td style="color:#446688">{i:02d}</td>
                        <td><span class="tag">{r['name']}</span></td>
                        <td><span class="expr">{r['expression']}</span></td>
                        <td><span class="result">{r['result']}</span></td>
                    </tr>
"""

html += f"""                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>由 Python {__import__('sys').version.split()[0]} 計算 · math 模組支援</p>
        </div>
    </div>
</body>
</html>
"""

output_path = r"D:\claude code 自動交易系統\calculator_result.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"計算完成！共 {len(results)} 項運算")
for r in results:
    print(f"  {r['name']:12s} | {r['expression']:30s} = {r['result']}")
print(f"\nHTML 已儲存至: {output_path}")
