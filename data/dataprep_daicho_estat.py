#############################################################
# データソース
# 住民基本台帳に基づく人口、人口動態及び世帯数調査
# https://www.e-stat.go.jp/stat-search/files?page=1&layout=datalist&toukei=00200241&tstat=000001039591&cycle=7&tclass1=000001039601&tclass2val=0
# https://www.soumu.go.jp/main_sosiki/jichi_gyousei/daityo/jinkou_jinkoudoutai-setaisuu.html
#############################################################

import pandas as pd
import requests
import io
from pathlib import Path

# --- 1. 設定エリア ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
PARQUET_DIR = DATA_DIR / 'parquet'
PARQUET_DIR.mkdir(parents=True, exist_ok=True)

# 年齢区分の固定リスト
AGE_COLS = [
    '総数', '0歳～4歳', '5歳～9歳', '10歳～14歳', '15歳～19歳', '20歳～24歳',
    '25歳～29歳', '30歳～34歳', '35歳～39歳', '40歳～44歳', '45歳～49歳',
    '50歳～54歳', '55歳～59歳', '60歳～64歳', '65歳～69歳', '70歳～74歳',
    '75歳～79歳', '80歳以上'
]

# 市区町村の合併・移行対応辞書
REMAP_DICT = {
    ("033057", "岩手郡滝沢村"): ("032166", "滝沢市"),
    ("044237", "黒川郡富谷町"): ("042161", "富谷市"),
    ("093670", "下都賀郡岩舟町"): ("092037", "栃木市"),
    ("403059", "筑紫郡那珂川町"): ("402311", "那珂川市"),
    ("221317", "浜松市中区"): ("221384", "浜松市中央区"),
    ("221325", "浜松市東区"): ("221384", "浜松市中央区"),
    ("221333", "浜松市西区"): ("221384", "浜松市中央区"),
    ("221341", "浜松市南区"): ("221384", "浜松市中央区"),
    ("221350", "浜松市北区（三方原）"): ("221384", "浜松市中央区"),
    ("221350", "浜松市北区"): ("221392", "浜松市浜名区"),
    ("221368", "浜松市浜北区"): ("221392", "浜松市浜名区"),
    ("221376", "浜松市天竜区"): ("221406", "浜松市天竜区"),
    ("282219", "篠山市"): ("282219", "丹波篠山市"), 
    ("134015", "八丈島　八丈町"): ("134015", "八丈町"), 
    ("133817", "三宅島　三宅村"): ("133817", "三宅村"), 
}

# --- 2. 補助関数 ---

def fetch_and_clean(year, url):
    """e-StatからExcelを取得し、共通フォーマットに整形する"""
    print(f"Processing: {year}")
    res = requests.get(url)
    df_raw = pd.read_excel(io.BytesIO(res.content), header=None)
    
    # ヘッダー行を特定
    header_idx = df_raw[df_raw.eq("都道府県名").any(axis=1)].index[0]
    df = pd.read_excel(io.BytesIO(res.content), skiprows=header_idx)
    
    df['year'] = year
    data_start_idx = 4 

    # 80歳以上の統合計算（詳細区分がある場合）
    if len(df.columns) > 25:
        target_cols = df.iloc[:, data_start_idx+17:data_start_idx+22]
        df['80歳以上'] = target_cols.apply(pd.to_numeric, errors='coerce').sum(axis=1)

    # 指定された位置からデータを取得
    new_df = df[['year', '団体コード', '都道府県名', '市区町村名', '性別']].copy()
    for i, col_name in enumerate(AGE_COLS):
        new_df[col_name] = df.iloc[:, data_start_idx + i]
    
    # クレンジング
    new_df = new_df.dropna(subset=['都道府県名'])
    return new_df[new_df['都道府県名'] != '都道府県名']

def update_city_info(row):
    """辞書に基づいて団体コードと市区町村名を更新する"""
    key = (row['団体コード'], row['市区町村名'])
    if key in REMAP_DICT:
        row['団体コード'], row['市区町村名'] = REMAP_DICT[key]
    return row

# --- 3. メイン処理 ---
############################
# 総人口
############################

links_total = [
    {"year":2025,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040306654&fileKind=0"},
    {"year":2024,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040306674&fileKind=0"},
    {"year":2023,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040306648&fileKind=0"},
    {"year":2022,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032224637&fileKind=0"},
    {"year":2021,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040306661&fileKind=0"},
    {"year":2020,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031971230&fileKind=0"},
    {"year":2019,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031843909&fileKind=0"},
    {"year":2018,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031736914&fileKind=0"},
    {"year":2017,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031598539&fileKind=0"},
    {"year":2016,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031429218&fileKind=0"},
    {"year":2015,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000030438669&fileKind=0"},
    {"year":2014,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000025711035&fileKind=0"},
    {"year":2013,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000022057246&fileKind=0"},
]

# ############################
# # 日本人人口
# ############################

links_japanese = [
    {"year":2025,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040306662&fileKind=0"},
    {"year":2024,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040306678&fileKind=0"},
    {"year":2023,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040306667&fileKind=0"},
    {"year":2022,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032224641&fileKind=0"},
    {"year":2021,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040306689&fileKind=0"},
    {"year":2020,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031971233&fileKind=0"},
    {"year":2019,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031843913&fileKind=0"},
    {"year":2018,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031736918&fileKind=0"},
    {"year":2017,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031598552&fileKind=0"},
    {"year":2016,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031429220&fileKind=0"},
    {"year":2015,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000030438670&fileKind=0"},
    {"year":2014,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000025711265&fileKind=0"},
    {"year":2013,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000022057231&fileKind=0"},
]

# ############################
# 外国人人口
# ############################

links_foreigner = [
    {"year":2025,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040306690&fileKind=0"},
    {"year":2024,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040306682&fileKind=0"},
    {"year":2023,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040306650&fileKind=0"},
    {"year":2022,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032224645&fileKind=0"},
    {"year":2021,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040306694&fileKind=0"},
    {"year":2020,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031971237&fileKind=0"},
    {"year":2019,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031843917&fileKind=0"},
    {"year":2018,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031736922&fileKind=0"},
    {"year":2017,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031598572&fileKind=0"},
    {"year":2016,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031429275&fileKind=0"},
    {"year":2015,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000030438864&fileKind=0"},
    {"year":2014,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000025711630&fileKind=0"},
    {"year":2013,"url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000022057458&fileKind=0"},
]


def generate_dtaframe(links):
    print('\n ---- generate dataframe ----')
    # データの取得と結合
    all_df = [fetch_and_clean(link['year'], link['url']) for link in links]
    final_df = pd.concat(all_df, ignore_index=True)

    # 縦持ち（Long Format）変換
    df_long = final_df.melt(
        id_vars=['year', '団体コード', '都道府県名', '市区町村名', '性別'], 
        value_vars=AGE_COLS, 
        var_name='年齢区分', 
        value_name='人口'
    )

    # --- 4. データクレンジング ---

    # 基本的な表記揺れ・欠損処理
    df_long['団体コード'] = df_long['団体コード'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '').str.zfill(6)
    df_long['都道府県名'] = df_long['都道府県名'].str.replace('*', '', regex=False)
    df_long['市区町村名'] = df_long['市区町村名'].str.replace('*', '', regex=False).fillna('-')

    # 人口の数値化
    df_long['人口'] = pd.to_numeric(df_long['人口'].replace(['-', '－'], '0'), errors='coerce').fillna(0).astype(int)

    # 合併対応の適用
    df_long = df_long.apply(update_city_info, axis=1)

    # エリアレベルのマージ（都道府県・市区町村名で紐付け）
    df_level = pd.read_csv(DATA_DIR / 'daicho' / 'dantai_code_w_name.csv')
    df_long = pd.merge(
        df_long, 
        df_level[['都道府県名', '市区町村名', 'エリアレベル']], 
        on=['都道府県名', '市区町村名'], 
        how="left"
    )

    # --- 5. 集計結果の確認 ---
    # 市区町村別
    df_filtered = df_long[
        (df_long['性別'] == '計') & 
        (df_long['年齢区分'] == '総数') &
        (df_long['エリアレベル'] == 'level3') 
    ]

    df_filtered = df_filtered.groupby(['year','団体コード','都道府県名','市区町村名']).sum()[['人口']].reset_index()

    return df_filtered

df_total = generate_dtaframe(links_total).rename(columns={'人口':'総人口'})
df_japanese = generate_dtaframe(links_japanese).rename(columns={'人口':'日本人人口'})
df_foreigner= generate_dtaframe(links_foreigner).rename(columns={'人口':'外国人人口'})
df = pd.merge(df_total,df_japanese, on=['year','団体コード','都道府県名','市区町村名'], how='left')
df = pd.merge(df,df_foreigner, on=['year','団体コード','都道府県名','市区町村名'], how='left')


# 確認用
print(df.columns)
print(f"\n集計対象行数: {len(df)}")
summary = df.groupby('year')[['総人口', '日本人人口','外国人人口']].sum()
summary['foreigner_check']=summary['総人口']-summary['日本人人口']
summary.loc[summary['foreigner_check'] == summary['外国人人口'], 'check'] = 1
print("\n--- 年度別人口（level3積み上げ） ---")
print(summary)

# --- 6. 保存 ---
output_path = PARQUET_DIR / "estat_daicho.parquet"
df.to_parquet(output_path, engine="pyarrow", index=False)

print(f"\n完了！ 保存先: {output_path}")


