import copy
import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
import matplotlib.colors as mcolors
from pathlib import Path
from constants import PREF_ORDER

_CMAP_JINKO = mcolors.LinearSegmentedColormap.from_list('jinko', ['#d73027', '#fee090', '#4575b4'])

# CSS読み込み
css_path = Path(__file__).parent / 'styles.css'
st.markdown(f'<style>{css_path.read_text()}</style>', unsafe_allow_html=True)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
GEO_DIR = DATA_DIR / 'geo'


@st.cache_data
def load_jinko_raw():
    """市区町村レベルの生データを返す。日本人人口列を追加。"""
    df = pd.read_csv(DATA_DIR / 'daicho_estat.csv')
    df['日本人人口'] = df['総人口'] - df['外国人人口']
    return df


@st.cache_data
def load_jinko_pref():
    """都道府県×年の集計データ（日本人人口・外国人人口含む）。"""
    df = load_jinko_raw()
    pref = df.groupby(['year', '都道府県名']).agg(
        総人口=('総人口', 'sum'),
        外国人人口=('外国人人口', 'sum'),
        日本人人口=('日本人人口', 'sum'),
    ).reset_index()
    pref['外国人比率'] = (pref['外国人人口'] / pref['総人口'] * 100).round(2)
    return pref


@st.cache_data
def load_geojson_jinko(path):
    with open(path) as f:
        return json.load(f)


df_raw = load_jinko_raw()
df_pref = load_jinko_pref()
years = sorted(df_pref['year'].unique())
base_year = years[0]    # 2013
latest_year = years[-1]  # 2025

# --- ページ ---
st.title('人口減少')
st.info(
    '**日本人人口**（総人口 − 外国人人口）の推移。'
    f'住民基本台帳（毎年**1月1日**基準）に基づく。'
    f'{base_year}年との比較で都道府県・市区町村ごとの増減を確認できる。'
    '人口減少・少子高齢化は、社会保障・財政・地域経済に直結する政策課題。'
    '\n\n**注**: 総務省が公表する推計人口（**10月1日**基準・国勢調査補正値）とは'
    '集計時点・方法が異なるため、数値に差異が生じる。',
    icon='ℹ️',
)

# 都道府県フィルター
pref_list = [p for p in PREF_ORDER if p in df_pref['都道府県名'].unique()]
selected_pref_raw = st.selectbox('都道府県を選択', ['全国'] + pref_list,
                                  label_visibility='collapsed', key='jinko_pref_filter')
selected_pref = None if selected_pref_raw == '全国' else selected_pref_raw

# 市区町村フィルター（都道府県選択時のみ）
selected_city = None
if selected_pref:
    city_list = sorted(
        df_raw[df_raw['都道府県名'] == selected_pref]['市区町村名'].unique()
    )
    selected_city_raw = st.selectbox('市区町村を選択', ['全市区町村'] + city_list,
                                      label_visibility='collapsed', key='jinko_city_filter')
    selected_city = None if selected_city_raw == '全市区町村' else selected_city_raw

# === 推移グラフ（日本人人口前年比 + 外国人人口）===
if selected_city:
    df_chart = df_raw[
        (df_raw['都道府県名'] == selected_pref) & (df_raw['市区町村名'] == selected_city)
    ].copy().sort_values('year')
    title_suffix = f'{selected_pref} {selected_city}'
elif selected_pref:
    df_chart = df_pref[df_pref['都道府県名'] == selected_pref].copy().sort_values('year')
    title_suffix = selected_pref
else:
    df_chart = df_pref.groupby('year').agg(
        日本人人口=('日本人人口', 'sum'),
        外国人人口=('外国人人口', 'sum'),
    ).reset_index().sort_values('year')
    title_suffix = '全国'

# === 積み上げ棒グラフ（日本人・外国人人口の実数推移）===
st.markdown(f'###### 日本人・外国人人口の推移（{title_suffix}）')
fig_stack = go.Figure()
fig_stack.add_trace(go.Bar(
    x=df_chart['year'], y=df_chart['日本人人口'],
    name='日本人人口', marker_color='#d73027',
))
fig_stack.add_trace(go.Bar(
    x=df_chart['year'], y=df_chart['外国人人口'],
    name='外国人人口', marker_color='#4575b4',
))
fig_stack.update_layout(
    barmode='stack',
    xaxis=dict(tickmode='linear', dtick=1, fixedrange=True, showgrid=False),
    yaxis=dict(title='人口（人）', fixedrange=True, tickformat=',', showgrid=False),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    margin=dict(l=10, r=10, t=30, b=10), height=280,
    dragmode=False,
)
st.plotly_chart(fig_stack, use_container_width=True,
                config={'displayModeBar': False, 'scrollZoom': False}, key='jinko_stack')

df_chart['日本人前年比'] = df_chart['日本人人口'].diff()
df_chart['外国人前年比'] = df_chart['外国人人口'].diff()
df_chart = df_chart[df_chart['日本人前年比'].notna()].copy()

st.markdown(f'###### 日本人・外国人人口の前年比増減（{title_suffix}）')
fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_chart['year'], y=df_chart['日本人前年比'],
    name='日本人人口 前年比増減',
    marker_color='#d73027',
))
fig.add_trace(go.Bar(
    x=df_chart['year'], y=df_chart['外国人前年比'],
    name='外国人人口 前年比増減',
    marker_color='#4575b4',
))
fig.update_layout(
    barmode='relative',
    xaxis=dict(tickmode='linear', dtick=1, fixedrange=True),
    yaxis=dict(title='前年比増減（人）', fixedrange=True, tickformat=','),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    margin=dict(l=10, r=10, t=30, b=10), height=280,
    dragmode=False,
)
st.plotly_chart(fig, use_container_width=True,
                config={'displayModeBar': False, 'scrollZoom': False}, key='jinko_jp_trend')

# === コロプレス地図 ===
if not selected_pref:
    # 都道府県別 日本人人口 基準年比
    df_base_jp = df_pref[df_pref['year'] == base_year][['都道府県名', '日本人人口']].rename(columns={'日本人人口': '基準人口'})
    df_latest_jp = df_pref[df_pref['year'] == latest_year].merge(df_base_jp, on='都道府県名')
    df_latest_jp['増減率'] = ((df_latest_jp['日本人人口'] - df_latest_jp['基準人口']) / df_latest_jp['基準人口'] * 100).round(1)
    df_latest_jp['増減数'] = df_latest_jp['日本人人口'] - df_latest_jp['基準人口']

    pref_geo_path = GEO_DIR / 'prefectures.geojson'
    if pref_geo_path.exists():
        geojson = load_geojson_jinko(str(pref_geo_path))
        geojson = copy.deepcopy(geojson)

        rate_map = dict(zip(df_latest_jp['都道府県名'], df_latest_jp['増減率']))
        jp_pop_map = dict(zip(df_latest_jp['都道府県名'], df_latest_jp['日本人人口']))
        change_map = dict(zip(df_latest_jp['都道府県名'], df_latest_jp['増減数']))
        for feat in geojson['features']:
            name = feat['properties'].get('都道府県', '')
            feat['properties']['増減率'] = rate_map.get(name, 0)
            feat['properties']['日本人人口'] = f"{jp_pop_map.get(name, 0):,}"
            feat['properties']['増減数'] = f"{change_map.get(name, 0):+,}"

        _abs = max(abs(min(rate_map.values())), abs(max(rate_map.values())))
        vmin, vmax = -_abs, _abs
        colormap = cm.LinearColormap(
            colors=['#d73027', '#fee090', '#4575b4'],
            vmin=vmin, vmax=vmax,
            caption=f'日本人人口増減率（{base_year}→{latest_year}年、%）',
        )
        colormap.width = 250

        m = folium.Map(location=[37, 137], zoom_start=5, tiles='cartodbpositron')
        m.fit_bounds([[24, 122], [46, 146]])

        def style_fn(feature):
            name = feature['properties'].get('都道府県', '')
            val = rate_map.get(name, 0)
            return {'fillColor': colormap(val), 'color': '#fff', 'weight': 0.5, 'fillOpacity': 0.75}

        folium.GeoJson(
            geojson,
            style_function=style_fn,
            highlight_function=lambda f: {'weight': 2, 'color': '#333', 'fillOpacity': 0.9},
            tooltip=folium.GeoJsonTooltip(
                fields=['都道府県', '日本人人口', '増減数', '増減率'],
                aliases=['', f'{latest_year}年日本人人口', f'{base_year}年比増減数', '増減率(%)'],
                sticky=True, style='font-size:13px;',
            ),
        ).add_to(m)
        colormap.add_to(m)
        st_folium(m, use_container_width=True, height=400, returned_objects=[])

elif selected_pref:
    # 都道府県別: 市区町村別コロプレス
    pref_idx = PREF_ORDER.index(selected_pref) + 1 if selected_pref in PREF_ORDER else None
    if pref_idx:
        city_geo_path = GEO_DIR / f'{pref_idx:02d}_{selected_pref}.geojson'
        if city_geo_path.exists():
            geojson_city = load_geojson_jinko(str(city_geo_path))
            geojson_city = copy.deepcopy(geojson_city)

            df_cb = df_raw[(df_raw['year'] == base_year) & (df_raw['都道府県名'] == selected_pref)][['市区町村名', '総人口']].rename(columns={'総人口': '基準人口'})
            df_cl = df_raw[(df_raw['year'] == latest_year) & (df_raw['都道府県名'] == selected_pref)][['市区町村名', '総人口']]
            df_cm = df_cl.merge(df_cb, on='市区町村名', how='left')
            df_cm['増減率'] = ((df_cm['総人口'] - df_cm['基準人口']) / df_cm['基準人口'] * 100).round(1)
            df_cm['増減数'] = df_cm['総人口'] - df_cm['基準人口']

            city_rate_map = dict(zip(df_cm['市区町村名'], df_cm['増減率']))
            city_pop_map = dict(zip(df_cm['市区町村名'], df_cm['総人口']))
            city_change_map = dict(zip(df_cm['市区町村名'], df_cm['増減数']))
            city_name_set = set(city_rate_map.keys())

            def resolve_city_jinko(geo_name, name_set):
                if geo_name in name_set:
                    return geo_name
                if '郡' in geo_name:
                    base = geo_name.split('郡', 1)[1]
                    if base in name_set:
                        return base
                return None

            for feat in geojson_city['features']:
                geo_name = feat['properties'].get('市区町村', '')
                matched = resolve_city_jinko(geo_name, city_name_set)
                rate = city_rate_map.get(matched) if matched else None
                pop = city_pop_map.get(matched) if matched else None
                change = city_change_map.get(matched) if matched else None
                feat['properties']['_rate'] = rate if rate is not None else 0
                feat['properties']['総人口'] = f"{int(pop):,}" if pop is not None else '-'
                feat['properties']['増減数'] = f"{int(change):+,}" if change is not None else '-'
                feat['properties']['増減率'] = f"{rate:+.1f}%" if rate is not None else '-'

            valid_rates = [v for v in city_rate_map.values() if pd.notna(v)]
            _abs_c = max(abs(min(valid_rates)), abs(max(valid_rates)))
            vmin_c, vmax_c = -_abs_c, _abs_c
            colormap_city = cm.LinearColormap(
                colors=['#d73027', '#fee090', '#4575b4'],
                vmin=vmin_c, vmax=vmax_c,
                caption=f'総人口増減率（{base_year}→{latest_year}年、%）',
            )
            colormap_city.width = 250

            coords = []
            for feat in geojson_city['features']:
                geo_name = feat['properties'].get('市区町村', '')
                matched = resolve_city_jinko(geo_name, city_name_set)
                if selected_city and matched != selected_city:
                    continue
                geom = feat['geometry']
                if geom['type'] == 'Polygon':
                    coords.extend(geom['coordinates'][0])
                elif geom['type'] == 'MultiPolygon':
                    for poly in geom['coordinates']:
                        coords.extend(poly[0])
            if not coords:
                for feat in geojson_city['features']:
                    geom = feat['geometry']
                    if geom['type'] == 'Polygon':
                        coords.extend(geom['coordinates'][0])
                    elif geom['type'] == 'MultiPolygon':
                        for poly in geom['coordinates']:
                            coords.extend(poly[0])
            lats = [c[1] for c in coords]
            lngs = [c[0] for c in coords]
            lat_c = (min(lats) + max(lats)) / 2
            lng_c = (min(lngs) + max(lngs)) / 2
            shrink = 2.0 if selected_city else 1.0
            lat_h = (max(lats) - min(lats)) / 2 * shrink
            lng_h = (max(lngs) - min(lngs)) / 2 * shrink
            m_city = folium.Map(
                location=[lat_c, lng_c],
                zoom_start=8, tiles='cartodbpositron',
            )
            m_city.fit_bounds([[lat_c - lat_h, lng_c - lng_h], [lat_c + lat_h, lng_c + lng_h]])

            def style_fn_city(feature, _rate_map=city_rate_map, _cm=colormap_city, _sel=selected_city):
                geo_name = feature['properties'].get('市区町村', '')
                matched = resolve_city_jinko(geo_name, city_name_set)
                rate = _rate_map.get(matched) if matched else None
                is_selected = bool(_sel and matched == _sel)
                if _sel and not is_selected:
                    return {'fillColor': 'transparent', 'color': 'transparent', 'weight': 0, 'fillOpacity': 0}
                return {
                    'fillColor': _cm(rate) if rate is not None else '#cccccc',
                    'color': '#fff',
                    'weight': 0.5,
                    'fillOpacity': 0.75,
                }

            folium.GeoJson(
                geojson_city,
                style_function=style_fn_city,
                highlight_function=lambda f: {'weight': 2, 'color': '#333', 'fillOpacity': 0.9},
                tooltip=folium.GeoJsonTooltip(
                    fields=['市区町村', '総人口', '増減数', '増減率'],
                    aliases=['', f'{latest_year}年総人口', f'{base_year}年比増減数', '増減率'],
                    sticky=True, style='font-size:13px;',
                ),
            ).add_to(m_city)
            colormap_city.add_to(m_city)
            st_folium(m_city, use_container_width=True, height=400, returned_objects=[])

# === テーブル ===
if selected_city:
    # 特定市区町村: 1行テーブル（基準年比）
    st.markdown(f'###### {selected_pref}の市区町村別総人口増減（{base_year}→{latest_year}年）')
    base_pop = df_raw[(df_raw['year'] == base_year) & (df_raw['都道府県名'] == selected_pref) & (df_raw['市区町村名'] == selected_city)]['総人口'].values
    latest_pop = df_raw[(df_raw['year'] == latest_year) & (df_raw['都道府県名'] == selected_pref) & (df_raw['市区町村名'] == selected_city)]['総人口'].values
    base_pop = base_pop[0] if len(base_pop) > 0 else None
    latest_pop = latest_pop[0] if len(latest_pop) > 0 else None
    増減数 = latest_pop - base_pop if base_pop and latest_pop else None
    増減率 = round(増減数 / base_pop * 100, 1) if base_pop and 増減数 is not None else None
    df_table = pd.DataFrame([{'市区町村': selected_city, '総人口': latest_pop, '増減数': 増減数, '増減率': 増減率}])
    _abs_t = max(abs(増減率), 0.1) if 増減率 is not None else 20
    styled = df_table.style.format({
        '総人口': '{:,.0f}',
        '増減数': '{:+,.0f}',
        '増減率': '{:+.1f}%',
    }).background_gradient(subset=['総人口'], cmap='Blues',
    ).background_gradient(subset=['増減率'], cmap=_CMAP_JINKO, vmin=-_abs_c, vmax=_abs_c,
    ).hide(axis='index')
    html = styled.to_html().replace('増減数', f'{base_year}年比増減数').replace('増減率', f'{base_year}年比増減率')
    st.markdown(f'<div class="custom-table">{html}</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 総務省 住民基本台帳に基づく人口（2025年1月）</p>', unsafe_allow_html=True)

elif selected_pref:
    # 都道府県内の市区町村別
    st.markdown(f'###### {selected_pref}の市区町村別総人口増減（{base_year}→{latest_year}年）')
    df_city_base = df_raw[(df_raw['year'] == base_year) & (df_raw['都道府県名'] == selected_pref)][
        ['市区町村名', '総人口']].rename(columns={'総人口': '基準人口'})
    df_city_latest = df_raw[(df_raw['year'] == latest_year) & (df_raw['都道府県名'] == selected_pref)][
        ['市区町村名', '総人口']].copy()
    df_table = df_city_latest.merge(df_city_base, on='市区町村名', how='left')
    df_table['増減数'] = df_table['総人口'] - df_table['基準人口']
    df_table['増減率'] = (df_table['増減数'] / df_table['基準人口'] * 100).round(1)
    df_table = df_table.rename(columns={'市区町村名': '市区町村'})[['市区町村', '総人口', '増減数', '増減率']]

    sort_opts = ['総人口', '増減数', '増減率']
    selected_sort = st.segmented_control('ソート順', sort_opts, default='総人口',
                                          label_visibility='collapsed', key='jinko_city_sort')
    if selected_sort is None or selected_sort == '総人口':
        df_table = df_table.sort_values('総人口', ascending=False)
    elif selected_sort == '増減数':
        df_table = df_table.sort_values('増減数')
    elif selected_sort == '増減率':
        df_table = df_table.sort_values('増減率')
    df_table = df_table.reset_index(drop=True)
    _abs_t = max(abs(df_table['増減率'].min()), abs(df_table['増減率'].max()))
    styled = df_table.style.format({
        '総人口': '{:,.0f}',
        '増減数': '{:+,.0f}',
        '増減率': '{:+.1f}%',
    }).background_gradient(subset=['総人口'], cmap='Blues',
    ).background_gradient(subset=['増減率'], cmap=_CMAP_JINKO, vmin=-_abs_t, vmax=_abs_t,
    ).hide(axis='index')
    html = styled.to_html().replace('増減数', f'{base_year}年比増減数').replace('増減率', f'{base_year}年比増減率')
    st.markdown(f'<div class="custom-table">{html}</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 総務省 住民基本台帳に基づく人口（2025年1月）</p>', unsafe_allow_html=True)

else:
    # 都道府県別（総人口ベース）
    st.markdown(f'###### 都道府県別総人口増減（{base_year}→{latest_year}年）')
    df_base_tot = df_pref[df_pref['year'] == base_year][['都道府県名', '総人口']].rename(columns={'総人口': '基準人口'})
    df_latest_tot = df_pref[df_pref['year'] == latest_year].merge(df_base_tot, on='都道府県名')
    df_latest_tot['増減数'] = df_latest_tot['総人口'] - df_latest_tot['基準人口']
    df_latest_tot['増減率'] = (df_latest_tot['増減数'] / df_latest_tot['基準人口'] * 100).round(1)
    df_table = df_latest_tot[['都道府県名', '総人口', '増減数', '増減率']].rename(columns={'都道府県名': '都道府県'})

    sort_opts = ['デフォルト', '総人口', '増減数', '増減率']
    selected_sort = st.segmented_control('ソート順', sort_opts, default='デフォルト',
                                          label_visibility='collapsed', key='jinko_pref_sort')
    if selected_sort is None:
        selected_sort = 'デフォルト'
    if selected_sort == 'デフォルト':
        pref_order_map = {p: i for i, p in enumerate(PREF_ORDER)}
        df_table = df_table.sort_values('都道府県', key=lambda s: s.map(pref_order_map))
    elif selected_sort == '総人口':
        df_table = df_table.sort_values('総人口', ascending=False)
    elif selected_sort == '増減数':
        df_table = df_table.sort_values('増減数')
    elif selected_sort == '増減率':
        df_table = df_table.sort_values('増減率')

    df_table = df_table.reset_index(drop=True)
    _abs_t = max(abs(df_table['増減率'].min()), abs(df_table['増減率'].max()))
    styled = df_table.style.format({
        '総人口': '{:,.0f}',
        '増減数': '{:+,.0f}',
        '増減率': '{:+.1f}%',
    }).background_gradient(subset=['総人口'], cmap='Blues',
    ).background_gradient(subset=['増減率'], cmap=_CMAP_JINKO, vmin=-_abs_t, vmax=_abs_t,
    ).hide(axis='index')
    html = styled.to_html().replace('増減数', f'{base_year}年比増減数').replace('増減率', f'{base_year}年比増減率')
    st.markdown(f'<div class="custom-table">{html}</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 総務省 住民基本台帳に基づく人口（2025年1月）</p>', unsafe_allow_html=True)
