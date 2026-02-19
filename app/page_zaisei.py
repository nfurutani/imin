import copy
import json
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
import matplotlib.colors as mcolors
from pathlib import Path
from constants import PREF_ORDER

_CMAP_ZAISEI = mcolors.LinearSegmentedColormap.from_list('zaisei', ['#d73027', '#fee090', '#4575b4'])
_CMAP_ZAISEI_R = mcolors.LinearSegmentedColormap.from_list('zaisei_r', ['#4575b4', '#fee090', '#d73027'])

# CSS読み込み
css_path = Path(__file__).parent / 'styles.css'
st.markdown(f'<style>{css_path.read_text()}</style>', unsafe_allow_html=True)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
GEO_DIR = DATA_DIR / 'geo'


@st.cache_data
def load_zaisei_pref():
    return pd.read_csv(DATA_DIR / 'zaisei_pref.csv')


@st.cache_data
def load_zaisei_city():
    return pd.read_csv(DATA_DIR / 'zaisei_city.csv')


@st.cache_data
def load_geojson_zaisei(path):
    with open(path) as f:
        return json.load(f)


df_pref = load_zaisei_pref()
df_city = load_zaisei_city()

st.title('財政力指数')
st.info(
    '**財政力指数**（3か年平均）: 自前の税収で歳出を賄える能力。'
    '**1.0以上**は地方交付税が不要な「不交付団体」。令和5年度時点で**1.0以上は東京都のみ**（1.10）。'
    '低いほど国からの交付税に依存し、国の政策に財政が左右されやすい。'
    '\n\n**経常収支比率**: 公務員給与・生活保護などの社会保障給付・借金返済といった'
    '毎年固定でかかる支出が、税収などの一般財源をどれだけ占めるかを示す。'
    '**90%超**ではほぼ裁量の余地がなく、新規政策に回せる予算がない状態。'
    '\n\n**実質公債費比率**（3か年平均）: 借金の元利返済額が一般財源に占める割合。'
    '**18%以上**で新規起債が制限され、**25%以上**で財政健全化計画の策定が義務付けられる。'
    '\n\n**将来負担比率**: 公営企業・第三セクター等の隠れ債務も含めた将来の財政負担の大きさ。'
    '**350%以上**で財政再生団体（実質的な財政破綻）のリスク。「−」は実質的に将来負担なし。',
    icon='ℹ️',
)

# 都道府県フィルター
pref_list = [p for p in PREF_ORDER if p in df_pref['都道府県名'].unique()]
selected_pref_raw = st.selectbox('都道府県を選択', ['全国'] + pref_list,
                                  label_visibility='collapsed', key='zaisei_pref_filter')
selected_pref = None if selected_pref_raw == '全国' else selected_pref_raw


def resolve_city_name(geo_name, fiscal_set, seirei_cities):
    """GeoJSONの市区町村名を財政データの団体名に対応付ける。"""
    if geo_name in fiscal_set:
        return geo_name
    # 郡プレフィックス除去: "上川郡剣淵町" → "剣淵町"
    if '郡' in geo_name:
        base = geo_name.split('郡', 1)[1]
        if base in fiscal_set:
            return base
    # 政令市区: "札幌市中央区" → "札幌市"
    for city in seirei_cities:
        if geo_name.startswith(city):
            return city
    return None


def render_choropleth_zaisei(geojson_data, val_map, caption, vmin, vmax, key_prop):
    geojson_data = copy.deepcopy(geojson_data)
    colormap = cm.LinearColormap(
        colors=['#d73027', '#fee090', '#4575b4'],
        vmin=vmin, vmax=vmax,
        caption=caption,
    )
    colormap.width = 250

    fiscal_set = set(val_map.keys())
    seirei_cities = sorted([k for k in fiscal_set if k.endswith('市')], key=len, reverse=True)

    for feat in geojson_data['features']:
        geo_name = feat['properties'].get(key_prop, '')
        matched = resolve_city_name(geo_name, fiscal_set, seirei_cities)
        val = val_map.get(matched, None) if matched else None
        feat['properties']['_val'] = round(val, 3) if val is not None else '-'

    coords = []
    for feat in geojson_data['features']:
        geom = feat['geometry']
        if geom['type'] == 'Polygon':
            coords.extend(geom['coordinates'][0])
        elif geom['type'] == 'MultiPolygon':
            for poly in geom['coordinates']:
                coords.extend(poly[0])

    lats = [c[1] for c in coords]
    lngs = [c[0] for c in coords]
    m = folium.Map(
        location=[(min(lats) + max(lats)) / 2, (min(lngs) + max(lngs)) / 2],
        zoom_start=5, tiles='cartodbpositron',
    )
    m.fit_bounds([[min(lats), min(lngs)], [max(lats), max(lngs)]])

    def style_fn(feature):
        geo_name = feature['properties'].get(key_prop, '')
        matched = resolve_city_name(geo_name, fiscal_set, seirei_cities)
        val = val_map.get(matched) if matched else None
        return {
            'fillColor': colormap(val) if val is not None else '#cccccc',
            'color': '#fff', 'weight': 0.5, 'fillOpacity': 0.75,
        }

    folium.GeoJson(
        geojson_data,
        style_function=style_fn,
        highlight_function=lambda f: {'weight': 2, 'color': '#333', 'fillOpacity': 0.9},
        tooltip=folium.GeoJsonTooltip(
            fields=[key_prop, '_val'],
            aliases=['', '財政力指数'],
            sticky=True, style='font-size:13px;',
        ),
    ).add_to(m)
    colormap.add_to(m)
    st_folium(m, use_container_width=True, height=400, returned_objects=[])


# === コロプレス地図 ===
if not selected_pref:
    # 全国: 都道府県別
    pref_geo_path = GEO_DIR / 'prefectures.geojson'
    if pref_geo_path.exists():
        geojson = load_geojson_zaisei(str(pref_geo_path))
        val_map = dict(zip(df_pref['都道府県名'], df_pref['財政力指数']))
        render_choropleth_zaisei(
            geojson, val_map,
            caption='財政力指数（令和5年度・3か年平均）',
            vmin=df_pref['財政力指数'].min(),
            vmax=df_pref['財政力指数'].max(),
            key_prop='都道府県',
        )
else:
    # 都道府県別: 市区町村別
    pref_idx = PREF_ORDER.index(selected_pref) + 1 if selected_pref in PREF_ORDER else None
    if pref_idx:
        city_geo_path = GEO_DIR / f'{pref_idx:02d}_{selected_pref}.geojson'
        if city_geo_path.exists():
            geojson = load_geojson_zaisei(str(city_geo_path))
            df_city_pref = df_city[df_city['都道府県名'] == selected_pref]
            val_map = dict(zip(df_city_pref['市区町村'], df_city_pref['財政力指数']))
            all_vals = df_city_pref['財政力指数'].dropna()
            render_choropleth_zaisei(
                geojson, val_map,
                caption='財政力指数（令和5年度・3か年平均）',
                vmin=all_vals.min(),
                vmax=all_vals.max(),
                key_prop='市区町村',
            )

# === テーブル ===
if selected_pref:
    st.markdown(f'###### 市区町村別主要財政指標（{selected_pref}・令和5年度）')
    df_table = df_city[df_city['都道府県名'] == selected_pref][
        ['市区町村', '財政力指数', '経常収支比率', '実質公債費比率', '将来負担比率']
    ].copy()
    sort_opts = ['財政力指数', '経常収支比率', '将来負担比率']
    selected_sort = st.segmented_control('ソート順', sort_opts, default='財政力指数',
                                          label_visibility='collapsed', key='zaisei_city_sort')
    if selected_sort is None or selected_sort == '財政力指数':
        df_table = df_table.sort_values('財政力指数', ascending=False)
    elif selected_sort == '経常収支比率':
        df_table = df_table.sort_values('経常収支比率', ascending=False)
    elif selected_sort == '将来負担比率':
        df_table = df_table.sort_values('将来負担比率', ascending=False)
    rename_col = '市区町村'
else:
    st.markdown('###### 都道府県別主要財政指標（令和5年度）')
    df_table = df_pref[['都道府県名', '財政力指数', '経常収支比率', '実質公債費比率', '将来負担比率']].copy()
    sort_opts = ['デフォルト', '財政力指数', '経常収支比率', '将来負担比率']
    selected_sort = st.segmented_control('ソート順', sort_opts, default='デフォルト',
                                          label_visibility='collapsed', key='zaisei_pref_sort')
    if selected_sort is None:
        selected_sort = 'デフォルト'
    if selected_sort == 'デフォルト':
        pref_order_map = {p: i for i, p in enumerate(PREF_ORDER)}
        df_table = df_table.sort_values('都道府県名', key=lambda s: s.map(pref_order_map))
    elif selected_sort == '財政力指数':
        df_table = df_table.sort_values('財政力指数', ascending=False)
    elif selected_sort == '経常収支比率':
        df_table = df_table.sort_values('経常収支比率', ascending=False)
    elif selected_sort == '将来負担比率':
        df_table = df_table.sort_values('将来負担比率', ascending=False)
    df_table = df_table.rename(columns={'都道府県名': '都道府県'})
    rename_col = '都道府県'

df_table = df_table.reset_index(drop=True)
display_cols = [rename_col, '財政力指数', '経常収支比率', '実質公債費比率', '将来負担比率']

styled = df_table[display_cols].style.format({
    '財政力指数': '{:.3f}',
    '経常収支比率': lambda v: f'{v:.1f}%' if pd.notna(v) else '-',
    '実質公債費比率': lambda v: f'{v:.1f}%' if pd.notna(v) else '-',
    '将来負担比率': lambda v: f'{v:.1f}%' if pd.notna(v) else '-',
}).background_gradient(subset=['財政力指数'], cmap=_CMAP_ZAISEI, vmin=0.2, vmax=1.1,
).background_gradient(subset=['経常収支比率'], cmap=_CMAP_ZAISEI_R, vmin=80, vmax=100,
).background_gradient(subset=['将来負担比率'], cmap=_CMAP_ZAISEI_R, vmin=0, vmax=350,
).hide(axis='index')

html = styled.to_html()
st.markdown(f'<div class="custom-table">{html}</div>', unsafe_allow_html=True)
st.markdown(
    '<p style="font-size:12px; color:gray; margin-top:-10px;">'
    'Source: 総務省 令和5年度地方公共団体の主要財政指標一覧｜'
    '経常収支比率・将来負担比率は高いほど財政硬直化・負担大。'
    '</p>',
    unsafe_allow_html=True,
)
