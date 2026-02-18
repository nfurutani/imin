import streamlit as st
import pandas as pd
import tab_zairyugaikokujin
from constants import COUNTRY_ORDER, PREF_ORDER


def render(data_dir):
    """国籍別タブ: フィルター + グラフ + 都道府県別テーブル"""
    # フィルター（一番上）- COUNTRY_ORDERの順序で表示
    df_country_long = pd.read_csv(data_dir / 'zairyu_pref_country.csv')
    available_countries = set(df_country_long['国籍'].unique()) - {'総数'}
    country_list = ['すべての国籍'] + [c for c in COUNTRY_ORDER if c in available_countries]
    selected_country = st.selectbox('国籍を選択', country_list, label_visibility='collapsed', key='country_tab_filter')

    # 総数をフィルターの下に表示
    filter_country = '総数' if selected_country == 'すべての国籍' else selected_country
    df_total_calc = df_country_long[df_country_long['国籍'] == filter_country].copy()
    df_total_calc = df_total_calc[df_total_calc['都道府県'] == '総数']
    df_total_pivot = df_total_calc.pivot(index='都道府県', columns='時点', values='人口').reset_index()
    total_pop = int(df_total_pivot['2025/06'].iloc[0])
    total_change = int(df_total_pivot['2025/06'].iloc[0] - df_total_pivot['2024/06'].iloc[0])
    total_rate = round(total_change / df_total_pivot['2024/06'].iloc[0] * 100, 1)
    st.markdown(f'<p style="font-size:14px; margin-bottom:5px;"><b>総数:</b> {total_pop:,}人　<b>増加数:</b> {total_change:+,}　<b>増加率:</b> {total_rate:+.1f}%</p>', unsafe_allow_html=True)

    # グラフ（国籍別在留外国人の推移 / 在留資格別在留外国人の推移）
    ext_country = None if selected_country == 'すべての国籍' else selected_country
    country_label = 'すべての国籍' if selected_country == 'すべての国籍' else selected_country
    tab_zairyugaikokujin.render(data_dir, key_prefix='country_tab', ext_country=ext_country, show_filter=False, country_mode=True, show_table=False, title_label=country_label)

    # 都道府県別テーブル
    st.markdown(f'###### 都道府県別外国人数 前年比（{country_label}）')

    df_country_by_pref = df_country_long[df_country_long['国籍'] == filter_country].copy()
    df_country_by_pref = df_country_by_pref[~df_country_by_pref['都道府県'].str.contains('※', na=False)]
    df_country_by_pref = df_country_by_pref.groupby(['都道府県', '時点'], as_index=False)['人口'].sum()
    df_country_pref_pivot = df_country_by_pref.pivot(index='都道府県', columns='時点', values='人口').reset_index()
    df_country_pref_pivot['増減数'] = df_country_pref_pivot['2025/06'] - df_country_pref_pivot['2024/06']
    df_country_pref_pivot['増減率'] = (df_country_pref_pivot['増減数'] / df_country_pref_pivot['2024/06'] * 100).round(1)
    df_country_pref_pivot = df_country_pref_pivot.rename(columns={'2025/06': '人口（2025）'})
    df_country_pref_pivot = df_country_pref_pivot[['都道府県', '人口（2025）', '増減数', '増減率']]

    # 総数を除外
    df_country_pref_pivot = df_country_pref_pivot[df_country_pref_pivot['都道府県'] != '総数'].copy()

    # ソート指標切り替え
    sort_metric_list = ['デフォルト', '人口', '増減数', '増減率']
    selected_sort_metric = st.segmented_control('ソート順', sort_metric_list, default='デフォルト',
                                                  label_visibility='collapsed', key='country_pref_sort_seg')
    if selected_sort_metric is None:
        selected_sort_metric = 'デフォルト'
    if selected_sort_metric == 'デフォルト':
        pref_order_map = {p: i for i, p in enumerate(PREF_ORDER)}
        df_country_pref_pivot = df_country_pref_pivot.sort_values('都道府県', key=lambda s: s.map(pref_order_map)).reset_index(drop=True)
    else:
        sort_col = '人口（2025）' if selected_sort_metric == '人口' else selected_sort_metric
        df_country_pref_pivot = df_country_pref_pivot.sort_values(sort_col, ascending=False).reset_index(drop=True)

    styled_country_pref = df_country_pref_pivot.style.format({
        '人口（2025）': '{:,.0f}',
        '増減数': '{:+,.0f}',
        '増減率': '{:+.1f}%'
    }).background_gradient(
        subset=['人口（2025）', '増減数', '増減率'],
        cmap='Blues'
    ).hide(axis='index')

    html_country_pref = f'<div class="custom-table">{styled_country_pref.to_html()}</div>'
    st.markdown(html_country_pref, unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 出入国在留管理庁 在留外国人統計（2025年6月）</p>', unsafe_allow_html=True)
