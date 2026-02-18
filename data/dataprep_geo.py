"""都道府県・市区町村のGeoJSON境界データを生成する。

Source: smartnews-smri/japan-topography (国土数値情報 行政区域データ N03)
"""
import json
import requests
import geopandas as gpd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
GEO_DIR = DATA_DIR / 'geo'
GEO_DIR.mkdir(exist_ok=True)

# 全国の市区町村GeoJSON (s0001 = 簡略化済み, ~1.6MB)
URL = 'https://raw.githubusercontent.com/smartnews-smri/japan-topography/main/data/municipality/geojson/s0001/N03-21_210101.json'

print('Downloading municipality GeoJSON...')
r = requests.get(URL, timeout=60)
r.raise_for_status()
gdf = gpd.GeoDataFrame.from_features(r.json()['features'], crs='EPSG:4326')
print(f'  {len(gdf)} features')


def make_city_name(row):
    """GeoJSON properties → 市区町村名 (solar dataの市区町村と一致する形式)"""
    n03_003 = row.get('N03_003') or ''
    n03_004 = row.get('N03_004') or ''
    # 政令指定都市: N03_003=札幌市, N03_004=中央区 → 札幌市中央区
    if n03_003.endswith('市'):
        return n03_003 + n03_004
    # 郡内町村: N03_003=稲敷郡, N03_004=河内町 → 稲敷郡河内町
    if n03_003.endswith('郡'):
        return n03_003 + n03_004
    # 一般市町村: N03_004=函館市 etc.
    return n03_004


gdf['市区町村'] = gdf.apply(make_city_name, axis=1)
gdf['都道府県'] = gdf['N03_001']

# --- 都道府県GeoJSON ---
print('Generating prefectures.geojson...')
pref_gdf = gdf.dissolve(by='都道府県').reset_index()
pref_gdf = pref_gdf[['都道府県', 'geometry']]
pref_gdf.to_file(GEO_DIR / 'prefectures.geojson', driver='GeoJSON')
print(f'  {len(pref_gdf)} prefectures')

# --- 市区町村GeoJSON (都道府県別) ---
PREF_ORDER = [
    '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
    '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
    '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県',
    '岐阜県', '静岡県', '愛知県', '三重県',
    '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県',
    '鳥取県', '島根県', '岡山県', '広島県', '山口県',
    '徳島県', '香川県', '愛媛県', '高知県',
    '福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県',
]

print('Generating per-prefecture city GeoJSON...')
for i, pref in enumerate(PREF_ORDER, 1):
    sub = gdf[gdf['都道府県'] == pref].copy()
    if sub.empty:
        continue
    city_gdf = sub.dissolve(by='市区町村').reset_index()
    city_gdf = city_gdf[['市区町村', 'geometry']]
    code = f'{i:02d}'
    out = GEO_DIR / f'{code}_{pref}.geojson'
    city_gdf.to_file(out, driver='GeoJSON')
    print(f'  {pref}: {len(city_gdf)} cities')

print('Done.')
