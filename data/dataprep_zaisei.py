"""
dataprep_zaisei.py
都道府県別・市区町村別主要財政指標（令和5年度）を取得してCSVに保存する。

Source:
    総務省 令和5年度地方公共団体の主要財政指標一覧
    https://www.soumu.go.jp/menu_seisaku/toukei/02zaisei07_04000131.html

Output:
    data/zaisei_pref.csv   — 都道府県別（47行）
    data/zaisei_city.csv   — 市区町村別（約1,741行）
"""

from pathlib import Path
import urllib.request
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
URL_PREF = 'https://www.soumu.go.jp/main_content/000983093.xlsx'
URL_CITY = 'https://www.soumu.go.jp/main_content/000983094.xlsx'
COLS_PREF = ['都道府県名', '財政力指数', '経常収支比率', '実質公債費比率', '将来負担比率', 'ラスパイレス指数']
COLS_CITY = ['団体コード', '都道府県名', '市区町村', '財政力指数', '経常収支比率', '実質公債費比率', '将来負担比率', 'ラスパイレス指数']
NUM_COLS = ['財政力指数', '経常収支比率', '実質公債費比率', '将来負担比率', 'ラスパイレス指数']


def main():
    tmp = DATA_DIR / '_zaisei_tmp.xlsx'

    # --- 都道府県別 ---
    print('Downloading prefecture data...')
    urllib.request.urlretrieve(URL_PREF, tmp)
    df_pref = pd.read_excel(tmp, sheet_name=0, header=None, skiprows=2)
    df_pref.columns = COLS_PREF
    df_pref = df_pref[df_pref['都道府県名'].notna() & ~df_pref['都道府県名'].str.contains('平均|合計', na=False)].copy()
    for col in NUM_COLS:
        df_pref[col] = pd.to_numeric(df_pref[col], errors='coerce')
    df_pref.reset_index(drop=True).to_csv(DATA_DIR / 'zaisei_pref.csv', index=False, encoding='utf-8-sig')
    print(f'Saved: zaisei_pref.csv ({len(df_pref)} rows)')

    # --- 市区町村別 ---
    print('Downloading city data...')
    urllib.request.urlretrieve(URL_CITY, tmp)
    df_city = pd.read_excel(tmp, sheet_name=0, header=None, skiprows=2)
    df_city.columns = COLS_CITY
    df_city = df_city[df_city['都道府県名'].notna()].copy()
    for col in NUM_COLS:
        df_city[col] = pd.to_numeric(df_city[col], errors='coerce')
    df_city.reset_index(drop=True).to_csv(DATA_DIR / 'zaisei_city.csv', index=False, encoding='utf-8-sig')
    print(f'Saved: zaisei_city.csv ({len(df_city)} rows)')

    tmp.unlink()


if __name__ == '__main__':
    main()
