import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# CSS読み込み
css_path = Path(__file__).parent / 'styles.css'
st.markdown(f'<style>{css_path.read_text()}</style>', unsafe_allow_html=True)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'

st.title('太陽光発電')

tab1, tab2 = st.tabs(['都道府県別', '地図'])

with tab1:
    df = pd.read_parquet(DATA_DIR / 'solar_pref_trend.parquet')

    # 時点をラベルに変換してソート
    def to_label(s):
        """2020.3 → 2020年3月, 2025.10 → 2025年10月"""
        parts = s.split('.')
        return f'{parts[0]}年{parts[1]}月'

    df['ラベル'] = df['時点'].apply(to_label)
    def sort_key(s):
        parts = s.split('.')
        return int(parts[0]) * 100 + int(parts[1])
    df['_sort'] = df['時点'].apply(sort_key)
    df = df.sort_values('_sort')
    label_order = df.drop_duplicates('ラベル')['ラベル'].tolist()

    # 都道府県フィルター（都道府県番号順）
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
    pref_list = ['全国'] + [p for p in PREF_ORDER if p in df['都道府県'].unique()]
    selected_pref = st.selectbox('都道府県を選択', pref_list, label_visibility='collapsed')

    if selected_pref == '全国':
        df_chart = df.groupby(['ラベル', '_sort'], as_index=False).agg(
            太陽光発電所数=('太陽光発電所数', 'sum'),
            太陽光最大出力kW=('太陽光最大出力kW', 'sum'),
        )
    else:
        df_chart = df[df['都道府県'] == selected_pref].copy()

    df_chart = df_chart.sort_values('_sort')
    df_chart['最大出力計'] = df_chart['太陽光最大出力kW'] / 1000

    fig = go.Figure()

    # バー: 発電所数
    fig.add_trace(go.Bar(
        x=df_chart['ラベル'], y=df_chart['太陽光発電所数'],
        name='発電所数',
        marker_color='#636EFA',
        yaxis='y',
        text=df_chart['太陽光発電所数'].apply(lambda x: f'{x:,.0f}'),
        textposition='inside',
        insidetextanchor='middle',
        textfont=dict(size=10),
    ))

    # ライン: 最大出力（MW）
    fig.add_trace(go.Scatter(
        x=df_chart['ラベル'], y=df_chart['最大出力計'],
        name='最大出力 (MW)',
        mode='lines+markers+text',
        line=dict(color='#FFA15A', width=2),
        marker=dict(size=8),
        yaxis='y2',
        text=df_chart['最大出力計'].apply(lambda x: f'{x:,.0f}'),
        textposition='top center',
        textfont=dict(size=10),
    ))

    fig.update_layout(
        xaxis=dict(categoryorder='array', categoryarray=label_order, fixedrange=True),
        yaxis=dict(title='発電所数', fixedrange=True, showgrid=False),
        yaxis2=dict(title='最大出力 (MW)', overlaying='y', side='right', fixedrange=True, showgrid=False),
        hovermode='x unified',
        height=450,
        margin=dict(l=40, r=40, t=50, b=30),
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='center', x=0.5),
        dragmode=False,
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

    # テーブル: 都道府県別 発電所数・最大出力（最新 vs 前回）
    latest = df['_sort'].max()
    prev = df[df['_sort'] < latest]['_sort'].max()
    df_latest = df[df['_sort'] == latest].set_index('都道府県')
    df_prev = df[df['_sort'] == prev].set_index('都道府県')

    df_table = pd.DataFrame({
        '都道府県': PREF_ORDER,
        '発電所数': [df_latest.loc[p, '太陽光発電所数'] if p in df_latest.index else 0 for p in PREF_ORDER],
        '発電所数（前回）': [df_prev.loc[p, '太陽光発電所数'] if p in df_prev.index else 0 for p in PREF_ORDER],
        '最大出力計': [df_latest.loc[p, '太陽光最大出力kW'] / 1000 if p in df_latest.index else 0 for p in PREF_ORDER],
        '最大出力計（前回）': [df_prev.loc[p, '太陽光最大出力kW'] / 1000 if p in df_prev.index else 0 for p in PREF_ORDER],
    })
    df_table['発電所増減率'] = ((df_table['発電所数'] / df_table['発電所数（前回）'] - 1) * 100).round(1)
    df_table['最大出力増減率'] = ((df_table['最大出力計'] / df_table['最大出力計（前回）'] - 1) * 100).round(1)
    df_table = df_table.rename(columns={'発電所数': '発電所'})
    df_table = df_table[['都道府県', '発電所', '発電所増減率', '最大出力計', '最大出力増減率']]

    latest_label = to_label(df[df['_sort'] == latest]['時点'].iloc[0])
    prev_label = to_label(df[df['_sort'] == prev]['時点'].iloc[0])
    st.markdown(f'###### 都道府県別（{latest_label} / 前回: {prev_label}）')

    # ソート切り替え
    sort_options = ['件数', '件数増減', '出力', '出力増減']
    selected_sort = st.segmented_control('ソート順', sort_options, default='件数',
                                          label_visibility='collapsed', key='solar_sort_seg')
    if selected_sort is None:
        selected_sort = '件数'
    sort_col_map = {'件数': '発電所', '件数増減': '発電所増減率', '出力': '最大出力計', '出力増減': '最大出力増減率'}
    df_table = df_table.sort_values(sort_col_map[selected_sort], ascending=False).reset_index(drop=True)

    styled = df_table.style.format({
        '発電所': '{:,.0f}',
        '発電所増減率': '{:+.1f}%',
        '最大出力計': '{:,.1f}',
        '最大出力増減率': '{:+.1f}%',
    }).background_gradient(
        subset=['発電所', '最大出力計'],
        cmap='OrRd',
    ).background_gradient(
        subset=['発電所増減率', '最大出力増減率'],
        cmap='OrRd',
    ).hide(axis='index')

    table_html = styled.to_html()
    table_html = (table_html
        .replace('発電所増減率', 'HATUDEN_ZOUGEN')
        .replace('最大出力増減率', 'SHUTSURYOKU_ZOUGEN')
        .replace('最大出力計', '最大出力<br>(MW)')
        .replace('>発電所<', '>発電所<br>(件数)<')
        .replace('HATUDEN_ZOUGEN', '発電所<br>(増減率)')
        .replace('SHUTSURYOKU_ZOUGEN', '最大出力<br>(増減率)')
    )
    html_table = f'<div class="custom-table">{table_html}</div>'
    st.markdown(html_table, unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 資源エネルギー庁 電力調査統計</p>', unsafe_allow_html=True)

with tab2:
    import folium
    from folium.plugins import FastMarkerCluster
    from streamlit_folium import st_folium

    df_map = pd.read_parquet(DATA_DIR / 'solar_nintei_city_map.parquet')

    # 指標切り替え
    map_metric = st.segmented_control('表示指標', ['件数', '出力(MW)'], default='件数',
                                       label_visibility='collapsed', key='solar_map_metric')
    if map_metric is None:
        map_metric = '件数'
    metric_col = '件数' if map_metric == '件数' else '合計出力MW'

    m = folium.Map(location=[36.5, 137.0], zoom_start=5, tiles='cartodbpositron')

    # FastMarkerCluster用のデータ（緯度経度のリスト）
    # 件数/出力に応じてCircleMarkerを使用（バブルマップ）
    max_val = df_map[metric_col].max()
    for _, row in df_map.iterrows():
        ratio = row[metric_col] / max_val
        radius = max(3, ratio * 30)
        popup_text = f"{row['都道府県名']}{row['市区町村名']}<br>件数: {row['件数']:,}<br>出力: {row['合計出力MW']:,.1f} MW"
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=radius,
            color='#e74c3c',
            fill=True,
            fill_color='#e74c3c',
            fill_opacity=0.5,
            weight=1,
            popup=folium.Popup(popup_text, max_width=200),
        ).add_to(m)

    st_folium(m, use_container_width=True, height=600)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: FIT制度 認定設備一覧（太陽光）</p>', unsafe_allow_html=True)
