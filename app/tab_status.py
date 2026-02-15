import streamlit as st
import pandas as pd
import tab_zairyugaikokujin
from constants import STATUS_ORDER


def render(data_dir):
    """在留資格別タブ: フィルター + グラフ + 都道府県別テーブル"""
    # フィルター（一番上）- STATUS_ORDERの順序で表示
    df_status_long = pd.read_csv(data_dir / 'zairyu_pref_status.csv')
    available_statuses = set(df_status_long['在留資格'].unique()) - {'総数'}
    status_list = ['すべての在留資格'] + [s for s in STATUS_ORDER if s in available_statuses]
    selected_status = st.selectbox('在留資格を選択', status_list, label_visibility='collapsed', key='status_tab_filter')

    # 総数をフィルターの下に表示
    filter_status = '総数' if selected_status == 'すべての在留資格' else selected_status
    df_total_calc = df_status_long[df_status_long['在留資格'] == filter_status].copy()
    df_total_calc = df_total_calc[df_total_calc['都道府県'] == '総数']
    df_total_pivot = df_total_calc.pivot(index='都道府県', columns='時点', values='人口').reset_index()
    total_pop = int(df_total_pivot['2025/06'].iloc[0])
    total_change = int(df_total_pivot['2025/06'].iloc[0] - df_total_pivot['2024/06'].iloc[0])
    total_rate = round(total_change / df_total_pivot['2024/06'].iloc[0] * 100, 1)
    st.markdown(f'<p style="font-size:14px; margin-bottom:5px;"><b>総数:</b> {total_pop:,}人　<b>増加数:</b> {total_change:+,}　<b>増加率:</b> {total_rate:+.1f}%</p>', unsafe_allow_html=True)

    # グラフ（地域別在留外国人の推移 / 在留資格グループ別の推移）
    # 在留資格のマッピング（pref_status → visa_group）
    status_to_visa_map = {
        '日本人の配偶者等': 'その他',
    }
    ext_visa = None
    if selected_status != 'すべての在留資格':
        ext_visa = status_to_visa_map.get(selected_status, selected_status)
    status_label = 'すべての資格' if selected_status == 'すべての在留資格' else selected_status
    tab_zairyugaikokujin.render(data_dir, key_prefix='status_tab', ext_visa=ext_visa, show_filter=False, country_mode=True, show_table=False, title_label=status_label)

    # 都道府県別テーブル
    st.markdown(f'###### 都道府県別外国人数 前年比（{status_label}）')

    df_status_by_pref = df_status_long[df_status_long['在留資格'] == filter_status].copy()
    df_status_by_pref = df_status_by_pref[~df_status_by_pref['都道府県'].str.contains('※', na=False)]
    df_status_by_pref = df_status_by_pref.groupby(['都道府県', '時点'], as_index=False)['人口'].sum()
    df_status_pref_pivot = df_status_by_pref.pivot(index='都道府県', columns='時点', values='人口').reset_index()
    df_status_pref_pivot['増減数'] = df_status_pref_pivot['2025/06'] - df_status_pref_pivot['2024/06']
    df_status_pref_pivot['増減率'] = (df_status_pref_pivot['増減数'] / df_status_pref_pivot['2024/06'] * 100).round(1)
    df_status_pref_pivot = df_status_pref_pivot.rename(columns={'2025/06': '人口（2025）'})
    df_status_pref_pivot = df_status_pref_pivot[['都道府県', '人口（2025）', '増減数', '増減率']]

    # 総数を除外
    df_status_pref_pivot = df_status_pref_pivot[df_status_pref_pivot['都道府県'] != '総数'].copy()

    # ソート指標切り替え
    status_sort_metric_list = ['人口', '増減数', '増減率']
    selected_status_sort_metric = st.segmented_control('ソート順', status_sort_metric_list, default='人口',
                                                         label_visibility='collapsed', key='status_pref_sort_seg')
    if selected_status_sort_metric is None:
        selected_status_sort_metric = '人口'
    status_sort_col = '人口（2025）' if selected_status_sort_metric == '人口' else selected_status_sort_metric
    df_status_pref_pivot = df_status_pref_pivot.sort_values(status_sort_col, ascending=False).reset_index(drop=True)

    styled_status_pref = df_status_pref_pivot.style.format({
        '人口（2025）': '{:,.0f}',
        '増減数': '{:+,.0f}',
        '増減率': '{:+.1f}%'
    }).background_gradient(
        subset=['人口（2025）', '増減数', '増減率'],
        cmap='BuGn'
    ).hide(axis='index')

    html_status_pref = f'<div class="custom-table">{styled_status_pref.to_html()}</div>'
    st.markdown(html_status_pref, unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 出入国在留管理庁 在留外国人統計（2025年6月）</p>', unsafe_allow_html=True)
