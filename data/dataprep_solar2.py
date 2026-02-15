import io
import requests
import pandas as pd
from pathlib import Path

links1 = {
    "2025": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2025/1-1-2025.xlsx",
    "2024": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2024/1-1-2024.xlsx",
    "2023": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2023/1-1-2023.xlsx",
    "2022": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2022/1-1-2022.xlsx",
    "2021": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2021/1-1-2021.xlsx",
    "2020": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2020/1-1-2020.xlsx",
    "2019": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2019/1-1-2019.xlsx",
}

links2 = {
    "2025": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2025/1-2-2025.xlsx",
    "2024": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2024/1-2-2024.xlsx",
    "2023": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2023/1-2-2023.xlsx",
    "2022": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2022/1-2-2022.xlsx",
    "2021": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2021/1-2-2021.xlsx",
    "2020": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2020/1-2-2020.xlsx",
    "2019": "https://www.enecho.meti.go.jp/statistics/electric_power/ep002/xls/2019/1-2-2019.xlsx",
}

HEADERS = {'User-Agent': 'Mozilla/5.0'}
DATA_DIR = Path(__file__).resolve().parent

rows = []
for year, url in sorted(links2.items()):
    print(f'{year}... ', end='', flush=True)
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    xls = pd.ExcelFile(io.BytesIO(r.content))

    # 各年度の最後のシート（年度末=3月）を使用
    sheet = xls.sheet_names[-1]
    df = pd.read_excel(xls, sheet_name=sheet, header=None)

    # 「太陽光」列を動的に検出（行2のヘッダーから）
    header_row2 = df.iloc[2]
    solar_col = None
    for col_idx, val in header_row2.items():
        if pd.notna(val) and '太陽光' in str(val):
            solar_col = col_idx
            break

    # solar_col = 発電所数、solar_col+1 = 最大出力計
    data = df.iloc[4:51, [0, solar_col, solar_col + 1]].copy()
    data.columns = ['都道府県', '太陽光発電所数', '太陽光最大出力kW']
    data['都道府県'] = data['都道府県'].str.strip()
    data['太陽光発電所数'] = pd.to_numeric(data['太陽光発電所数'], errors='coerce')
    data['太陽光最大出力kW'] = pd.to_numeric(data['太陽光最大出力kW'], errors='coerce')
    data['時点'] = sheet
    rows.append(data)
    print(f'{sheet} ({len(data)}件)')

df_all = pd.concat(rows, ignore_index=True)

# 発電所数の推移（都道府県×時点）
df_count = df_all.pivot(index='都道府県', columns='時点', values='太陽光発電所数')
# 最大出力計の推移（都道府県×時点）
df_output = df_all.pivot(index='都道府県', columns='時点', values='太陽光最大出力kW')

df_all.to_parquet(DATA_DIR / 'solar_pref_trend.parquet', index=False)
print(f'\n保存: solar_pref_trend.parquet ({len(df_all):,}件)')
print(f'\n太陽光発電所数（都道府県×時点）:')
print(df_count.head())
print(f'\n太陽光最大出力kW（都道府県×時点）:')
print(df_output.head())
