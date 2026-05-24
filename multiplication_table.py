from datetime import datetime
import sys

rows = []
for i in range(1, 10):
    row = []
    for j in range(1, 10):
        row.append((i, j, i * j))
    rows.append(row)

def color_for(val):
    ratio = (val - 1) / 80
    r = int(191 - ratio * 130)
    g = int(219 - ratio * 100)
    b = int(254 - ratio * 40)
    return f"rgb({r},{g},{b})"

cells_html = ""
for i, row in enumerate(rows):
    cells_html += "                <tr>\n"
    cells_html += f'                    <td class="row-header">{i+1}</td>\n'
    for (a, b, product) in row:
        bg = color_for(product)
        cells_html += f'                    <td style="background:{bg}" title="{a} \xd7 {b} = {product}">\n'
        cells_html += f'                        <span class="expr">{a}\xd7{b}</span>\n'
        cells_html += f'                        <span class="prod">{product}</span>\n'
        cells_html += f'                    </td>\n'
    cells_html += "                </tr>\n"

col_headers = "".join(f'                    <th>{j}</th>\n' for j in range(1, 10))
total = sum(a * b for row in rows for a, b, _ in row)

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>九九乘法表</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
            padding: 40px 20px;
            color: #1a1a2e;
        }}
        .container {{ max-width: 860px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 36px; }}
        .header h1 {{
            font-size: 2.8rem;
            font-weight: 800;
            background: linear-gradient(90deg, #0077cc, #7c3aed, #0077cc);
            background-size: 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: shimmer 3s linear infinite;
            margin-bottom: 8px;
        }}
        @keyframes shimmer {{
            0% {{ background-position: 0% center; }}
            100% {{ background-position: 200% center; }}
        }}
        .header p {{ color: #6b7280; font-size: 0.9rem; }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 32px;
            flex-wrap: wrap;
        }}
        .stat {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 14px 28px;
            text-align: center;
            min-width: 130px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .stat .val {{ font-size: 1.7rem; font-weight: 700; color: #0077cc; }}
        .stat .lbl {{ font-size: 0.78rem; color: #9ca3af; margin-top: 2px; }}
        .table-wrap {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        }}
        table {{ width: 100%; border-collapse: collapse; }}
        thead th {{
            background: #f0f6ff;
            color: #0077cc;
            font-size: 0.95rem;
            font-weight: 700;
            padding: 14px 0;
            border-bottom: 1px solid #dbeafe;
            text-align: center;
        }}
        thead th:first-child {{
            color: #7c3aed;
            background: #f5f0ff;
            width: 52px;
        }}
        td {{
            text-align: center;
            padding: 6px 4px;
            border: 1px solid rgba(255,255,255,0.04);
            transition: transform 0.15s, box-shadow 0.15s;
            cursor: default;
        }}
        td:hover {{
            transform: scale(1.15);
            z-index: 10;
            position: relative;
            box-shadow: 0 4px 20px rgba(0,0,0,0.6);
        }}
        .row-header {{
            background: #f5f0ff !important;
            color: #7c3aed !important;
            font-weight: 700;
            font-size: 0.95rem;
            border-right: 1px solid #e9d5ff !important;
            width: 52px;
        }}
        .expr {{
            display: block;
            font-size: 0.68rem;
            color: rgba(0,0,0,0.35);
            line-height: 1.2;
        }}
        .prod {{
            display: block;
            font-size: 1.1rem;
            font-weight: 700;
            color: #1a1a2e;
            line-height: 1.3;
        }}
        .legend {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
            margin-top: 28px;
            font-size: 0.82rem;
            color: #9ca3af;
        }}
        .legend-bar {{
            width: 180px;
            height: 10px;
            border-radius: 5px;
            background: linear-gradient(90deg, #bfdbfe, #93c5fd, #60a5fa, #3b82f6, #1d4ed8);
            border: 1px solid #e2e8f0;
        }}
        .footer {{
            text-align: center;
            margin-top: 24px;
            color: #9ca3af;
            font-size: 0.82rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>九九乘法表</h1>
            <p>生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        <div class="stats">
            <div class="stat"><div class="val">81</div><div class="lbl">總格數</div></div>
            <div class="stat"><div class="val">1</div><div class="lbl">最小值 (1\xd71)</div></div>
            <div class="stat"><div class="val">81</div><div class="lbl">最大值 (9\xd79)</div></div>
            <div class="stat"><div class="val">{total}</div><div class="lbl">所有積之和</div></div>
        </div>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>\xd7</th>
{col_headers}                    </tr>
                </thead>
                <tbody>
{cells_html}                </tbody>
            </table>
        </div>
        <div class="legend">
            <span>小 (1)</span>
            <div class="legend-bar"></div>
            <span>大 (81)</span>
        </div>
        <div class="footer">
            <p>由 Python {sys.version.split()[0]} 生成 &nbsp;\xb7&nbsp; 所有積之和 = (1+2+⋯+9)² = 45² = {45**2}</p>
        </div>
    </div>
</body>
</html>
"""

output_path = r"D:\claude code 自動交易系統\multiplication_table.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print("九九乘法表")
print("=" * 57)
for row in rows:
    line = "  ".join(f"{a}\xd7{b}={a*b:2d}" for a, b, _ in row)
    print(line)
print("=" * 57)
print(f"所有積之和：{total}  (= 45^2 = {45**2})")
print(f"\nHTML 已儲存至: {output_path}")
