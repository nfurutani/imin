import streamlit as st
import pandas as pd
import copy
import json
import unicodedata
from collections import defaultdict
from pathlib import Path
import folium
from streamlit_folium import st_folium
import branca.colormap as cm

# CSS読み込み
css_path = Path(__file__).parent / 'styles.css'
st.markdown(f'<style>{css_path.read_text()}</style>', unsafe_allow_html=True)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'

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


@st.cache_data
def load_mega_solar():
    df = pd.read_parquet(DATA_DIR / 'solar_nintei.parquet')
    df = df[df['発電設備区分'].str.contains('太陽光', na=False)].copy()
    df['出力kW'] = pd.to_numeric(df['太陽電池の合計出力kW'], errors='coerce').fillna(0)
    df = df[df['出力kW'] >= 1000].copy()

    # 市区町村名の抽出
    cities_df = pd.read_csv(DATA_DIR / 'daicho' / 'dantai_code_w_name.csv')
    level3 = cities_df[cities_df['エリアレベル'] == 'level3']
    level2 = cities_df[cities_df['エリアレベル'] == 'level2']

    pref_cities_l3 = defaultdict(list)
    for _, row in level3.iterrows():
        pref_cities_l3[row['都道府県名']].append(row['市区町村名'])
    for pref in pref_cities_l3:
        pref_cities_l3[pref].sort(key=len, reverse=True)

    # level2 fallback (政令指定都市など)
    pref_cities_l2 = defaultdict(list)
    for _, row in level2.iterrows():
        pref_cities_l2[row['都道府県名']].append(row['市区町村名'])
    for pref in pref_cities_l2:
        pref_cities_l2[pref].sort(key=len, reverse=True)

    def extract_city(pref, addr):
        addr = unicodedata.normalize('NFKC', str(addr))
        if addr.startswith(pref):
            addr = addr[len(pref):]
        # level3 最長一致
        for name in pref_cities_l3.get(pref, []):
            if addr.startswith(name):
                return name
        # 郡付き住所: 郡の後ろでマッチ
        if '郡' in addr:
            rest = addr.split('郡', 1)[1]
            for name in pref_cities_l3.get(pref, []):
                if rest.startswith(name):
                    return name
        # level2 fallback (旧区名など → 親市)
        for name in pref_cities_l2.get(pref, []):
            if addr.startswith(name):
                return name
        return None

    df['市区町村'] = df.apply(lambda r: extract_city(r['都道府県'], r['代表住所']), axis=1)

    # 調達期間終了年月をパース
    def parse_end_ym(s):
        try:
            parts = s.replace('年', ' ').replace('月', '').split()
            return pd.Timestamp(year=int(parts[0]), month=int(parts[1]), day=1)
        except Exception:
            return pd.NaT

    df['_調達終了'] = df['調達期間終了年月'].apply(parse_end_ym)
    return df


df_nintei = load_mega_solar()
today = pd.Timestamp.today().normalize()

st.title('メガソーラー')
st.caption('太陽電池の合計出力 ≥ 1MW（1,000kW）の太陽光発電設備')

# 都道府県フィルター
available_prefs = ['全国'] + [p for p in PREF_ORDER if p in df_nintei['都道府県'].unique()]
selected_pref_raw = st.selectbox('都道府県を選択', available_prefs,
                                  label_visibility='collapsed', key='solar_pref_filter')
selected_pref = None if selected_pref_raw == '全国' else selected_pref_raw

# フィルタ適用
if selected_pref:
    df_view = df_nintei[df_nintei['都道府県'] == selected_pref]
else:
    df_view = df_nintei

# 運転終了 / 運転中 / 運転予定 に分類
df_ended = df_view[df_view['_調達終了'].notna() & (df_view['_調達終了'] < today)]
df_rest = df_view[~df_view.index.isin(df_ended.index)]
df_operating = df_rest[df_rest['運転開始報告年月'] != '-']
df_planned = df_rest[df_rest['運転開始報告年月'] == '-']

status_options = [
    f'運転中（{len(df_operating):,}件）',
    f'運転予定（{len(df_planned):,}件）',
    f'運転終了（{len(df_ended):,}件）',
]
status_label = st.radio('ステータス', status_options,
                        horizontal=True, label_visibility='collapsed', key='solar_status_radio')
if status_label.startswith('運転終了'):
    df_target = df_ended
elif status_label.startswith('運転予定'):
    df_target = df_planned
else:
    df_target = df_operating

# コロプレス地図
GEO_DIR = DATA_DIR / 'geo'


@st.cache_data
def load_geojson(path):
    with open(path) as f:
        return json.load(f)


def render_choropleth(geojson_data, agg_data, key_col):
    """コロプレス地図を描画する。"""
    geojson_data = copy.deepcopy(geojson_data)
    value_map = dict(zip(agg_data[key_col], agg_data['合計出力kW']))
    if not value_map:
        return

    count_map = dict(zip(agg_data[key_col], agg_data['件数']))

    # featureにプロパティ追加
    for feat in geojson_data['features']:
        name = feat['properties'].get(key_col, '')
        mw = value_map.get(name, 0) / 1_000
        feat['properties']['出力MW'] = round(mw, 1)
        feat['properties']['件数'] = count_map.get(name, 0)

    vmin = min(value_map.values())
    vmax = max(value_map.values())
    colormap = cm.LinearColormap(
        colors=['#fee0d2', '#fc9272', '#de2d26'],
        vmin=vmin / 1_000, vmax=vmax / 1_000,
        caption='合計出力 (MW)',
    )
    colormap.width = 250

    # 地図の中心を計算
    coords = []
    for feat in geojson_data['features']:
        name = feat['properties'].get(key_col, '')
        if name in value_map:
            geom = feat['geometry']
            if geom['type'] == 'Polygon':
                coords.extend(geom['coordinates'][0])
            elif geom['type'] == 'MultiPolygon':
                for poly in geom['coordinates']:
                    coords.extend(poly[0])
    if not coords:
        return
    lats = [c[1] for c in coords]
    lngs = [c[0] for c in coords]

    m = folium.Map(
        location=[(min(lats) + max(lats)) / 2, (min(lngs) + max(lngs)) / 2],
        zoom_start=5, tiles='cartodbpositron',
    )
    m.fit_bounds([[min(lats), min(lngs)], [max(lats), max(lngs)]])

    def style_fn(feature):
        name = feature['properties'].get(key_col, '')
        val = value_map.get(name, 0)
        return {
            'fillColor': colormap(val / 1_000) if val > 0 else '#f0f0f0',
            'color': '#999',
            'weight': 0.5,
            'fillOpacity': 0.7,
        }

    folium.GeoJson(
        geojson_data,
        style_function=style_fn,
        highlight_function=lambda f: {'weight': 2, 'color': '#333', 'fillOpacity': 0.9},
        tooltip=folium.GeoJsonTooltip(
            fields=[key_col, '件数', '出力MW'],
            aliases=['', '件数', '出力(MW)'],
            localize=True,
            sticky=True,
            style='font-size:13px;',
        ),
    ).add_to(m)
    colormap.add_to(m)

    st_folium(m, use_container_width=True, height=400, returned_objects=[])


# 地図の集計データ（ソート前）
map_agg = df_target.groupby('都道府県' if not selected_pref else '市区町村').agg(
    件数=('設備ID', 'count'),
    合計出力kW=('出力kW', 'sum'),
).reset_index()

if selected_pref:
    geo_path = None
    pref_idx = PREF_ORDER.index(selected_pref) + 1 if selected_pref in PREF_ORDER else None
    if pref_idx:
        geo_path = GEO_DIR / f'{pref_idx:02d}_{selected_pref}.geojson'
    if geo_path and geo_path.exists():
        geojson = load_geojson(str(geo_path))
        render_choropleth(geojson, map_agg, '市区町村')
else:
    pref_geo = GEO_DIR / 'prefectures.geojson'
    if pref_geo.exists():
        geojson = load_geojson(str(pref_geo))
        render_choropleth(geojson, map_agg, '都道府県')

# 集計
if selected_pref:
    # 市区町村別
    group_col = '市区町村'
    agg = df_target.groupby(group_col).agg(
        件数=('設備ID', 'count'),
        合計出力kW=('出力kW', 'sum'),
    ).reset_index()
    agg['合計出力MW'] = (agg['合計出力kW'] / 1_000).round(1)
    agg = agg.sort_values('合計出力kW', ascending=False).reset_index(drop=True)
else:
    # 都道府県別
    group_col = '都道府県'
    pref_order_map = {p: i for i, p in enumerate(PREF_ORDER)}
    agg = df_target.groupby(group_col).agg(
        件数=('設備ID', 'count'),
        合計出力kW=('出力kW', 'sum'),
    ).reset_index()
    agg['合計出力MW'] = (agg['合計出力kW'] / 1_000).round(1)
    agg['_order'] = agg['都道府県'].map(pref_order_map)
    agg = agg.sort_values('_order').reset_index(drop=True)

# ソート
sort_opts = ['デフォルト', '件数', '出力']
selected_sort = st.segmented_control('ソート順', sort_opts, default='デフォルト',
                                      label_visibility='collapsed', key='solar_nintei_sort')
if selected_sort is None:
    selected_sort = 'デフォルト'
if selected_sort == '件数':
    agg = agg.sort_values('件数', ascending=False).reset_index(drop=True)
elif selected_sort == '出力':
    agg = agg.sort_values('合計出力kW', ascending=False).reset_index(drop=True)

disp = agg[[group_col, '件数', '合計出力MW']].copy()
styled = disp.style.format({
    '件数': '{:,.0f}',
    '合計出力MW': '{:,.1f}',
}).background_gradient(
    subset=['件数', '合計出力MW'],
    cmap='OrRd',
).hide(axis='index')
html = styled.to_html().replace('合計出力MW', '合計出力<br>(MW)')
st.markdown(f'<div class="custom-table">{html}</div>', unsafe_allow_html=True)

# Top10 ランキング（個別設備）
st.markdown('###### 発電設備別Top20')
top20 = (df_target[['発電事業者名', '都道府県', '市区町村', '出力kW']]
    .sort_values('出力kW', ascending=False)
    .head(20)
    .reset_index(drop=True))
top20['合計出力MW'] = (top20['出力kW'] / 1_000).round(1)
top20 = top20.drop(columns=['出力kW'])

styled_top = top20.style.format({
    '合計出力MW': '{:,.1f}',
}).background_gradient(
    subset=['合計出力MW'],
    cmap='OrRd',
).hide(axis='index')
html_top = styled_top.to_html().replace('合計出力MW', '合計出力<br>(MW)')
st.markdown(f'<div class="custom-table">{html_top}</div>', unsafe_allow_html=True)

st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 再生可能エネルギー発電事業計画 認定情報（認定設備一覧）</p>', unsafe_allow_html=True)
