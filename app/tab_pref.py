import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from constants import COUNTRY_ORDER, STATUS_ORDER


def render(data_dir):
    """都道府県別タブ: 外国人数推移 + 都道府県別比率 + 国籍別・在留資格別グラフ"""
    # 都道府県リストをCSVから取得（都道府県番号順）
    df_daicho_all = pd.read_csv(data_dir / 'daicho_estat.csv')
    df_daicho_all['pref_code'] = df_daicho_all['団体コード'].astype(str).str.zfill(6).str[:2]
    pref_list = df_daicho_all[['pref_code', '都道府県名']].drop_duplicates().sort_values('pref_code')['都道府県名'].tolist()
    selected_pref = st.selectbox('都道府県を選択', ['全国'] + pref_list, label_visibility='collapsed', key='tab_pref_select')
    pref_filter = '総数' if selected_pref == '全国' else selected_pref

    # 1. 外国人数・比率推移グラフ
    if selected_pref == '全国':
        st.markdown('###### 外国人数・比率推移（全国）')
        df_chart = df_daicho_all.groupby('year').agg({'総人口': 'sum', '外国人人口': 'sum'}).reset_index()
    else:
        st.markdown(f'###### 外国人数・比率推移（{selected_pref}）')
        df_chart = df_daicho_all[df_daicho_all['都道府県名'] == selected_pref].groupby('year').agg({'総人口': 'sum', '外国人人口': 'sum'}).reset_index()

    df_chart['比率'] = round(df_chart['外国人人口'] / df_chart['総人口'] * 100, 2)
    df_chart['外国人人口（万人）'] = df_chart['外国人人口'] / 10000

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(
        x=df_chart['year'], y=df_chart['外国人人口（万人）'],
        name='外国人数（万人）', marker_color='#636EFA', yaxis='y',
    ))
    fig_trend.add_trace(go.Scatter(
        x=df_chart['year'], y=df_chart['比率'],
        name='外国人比率（%）', mode='lines+markers',
        line=dict(color='#EF553B', width=2), marker=dict(size=5), yaxis='y2',
    ))
    fig_trend.update_layout(
        yaxis=dict(title='', showgrid=False, automargin=False, fixedrange=True),
        yaxis2=dict(title='', showgrid=False, overlaying='y', side='right', automargin=False, fixedrange=True, ticksuffix='%'),
        xaxis=dict(fixedrange=True, dtick=1),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5,
                    itemclick=False, itemdoubleclick=False),
        margin=dict(l=30, r=30, t=30, b=30), height=320,
        dragmode=False,
    )
    st.plotly_chart(fig_trend, use_container_width=True, key='pref_trend_chart', config={'displayModeBar': False, 'scrollZoom': False})
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 総務省 住民基本台帳に基づく人口</p>', unsafe_allow_html=True)

    # 2. 都道府県別 / 市区町村別外国人比率テーブル
    max_year = df_daicho_all['year'].max()
    prev_year = max_year - 1
    df_current = df_daicho_all[df_daicho_all['year'] == max_year]
    df_prev = df_daicho_all[df_daicho_all['year'] == prev_year]

    if selected_pref == '全国':
        st.markdown('###### 都道府県別外国人比率')
        # 都道府県別に集計（今年）
        df_curr_agg = df_current.groupby('都道府県名').agg({'総人口': 'sum', '外国人人口': 'sum'}).reset_index()
        # 都道府県別に集計（前年）
        df_prev_agg = df_prev.groupby('都道府県名').agg({'外国人人口': 'sum'}).reset_index()
        df_prev_agg = df_prev_agg.rename(columns={'外国人人口': '外国人_前年'})
        # マージ
        df_display = df_curr_agg.merge(df_prev_agg, on='都道府県名', how='left')
        df_display['比率'] = round(df_display['外国人人口'] / df_display['総人口'] * 100, 1)
        df_display['前年比'] = round((df_display['外国人人口'] - df_display['外国人_前年']) / df_display['外国人_前年'] * 100, 1)
        df_display = df_display.rename(columns={'都道府県名': '都道府県', '外国人人口': '外国人'})
        display_cols = ['都道府県', '総人口', '外国人', '比率', '前年比']
    else:
        st.markdown(f'###### {selected_pref}の市区町村別外国人比率')
        df_curr_pref = df_current[df_current['都道府県名'] == selected_pref].copy()
        df_prev_pref = df_prev[df_prev['都道府県名'] == selected_pref][['市区町村名', '外国人人口']].copy()
        df_prev_pref = df_prev_pref.rename(columns={'外国人人口': '外国人_前年'})
        # マージ
        df_display = df_curr_pref.merge(df_prev_pref, on='市区町村名', how='left')
        df_display['比率'] = round(df_display['外国人人口'] / df_display['総人口'] * 100, 1)
        df_display['前年比'] = round((df_display['外国人人口'] - df_display['外国人_前年']) / df_display['外国人_前年'] * 100, 1)
        df_display = df_display.rename(columns={'都道府県名': '都道府県', '市区町村名': '市区町村', '外国人人口': '外国人'})
        display_cols = ['市区町村', '総人口', '外国人', '比率', '前年比']

    # ソート指標切り替え
    sort_options = ['デフォルト', '総人口', '外国人', '比率', '前年比']
    selected_sort = st.segmented_control('ソート順', sort_options, default='デフォルト',
                                          label_visibility='collapsed', key='pref_table_sort_seg')
    if selected_sort is None:
        selected_sort = 'デフォルト'
    if selected_sort == 'デフォルト':
        if selected_pref == '全国':
            pref_order_map = {p: i for i, p in enumerate(pref_list)}
            df_display = df_display.sort_values('都道府県', key=lambda s: s.map(pref_order_map))
    else:
        df_display = df_display.sort_values(selected_sort, ascending=False)

    df_styled = df_display[display_cols].reset_index(drop=True)

    styled = df_styled.style.format({
        '総人口': '{:,.0f}',
        '外国人': '{:,.0f}',
        '比率': '{:.1f}',
        '前年比': '{:+.1f}%'
    }).background_gradient(
        subset=['総人口', '外国人', '比率', '前年比'],
        cmap='Purples'
    ).hide(axis='index')

    html = f'<div class="custom-table">{styled.to_html()}</div>'
    st.markdown(html, unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 総務省 住民基本台帳に基づく人口（2025年1月）</p>', unsafe_allow_html=True)

    # 3. 国籍別人口（前年比）バーグラフ
    st.markdown(f'###### {selected_pref}の国籍別人口と増減（前年比）')
    df_country_long = pd.read_csv(data_dir / 'zairyu_pref_country.csv')
    df_country_chart = df_country_long[df_country_long['都道府県'] == pref_filter].copy()

    # ピボットして2024/06と2025/06を横に並べる
    df_country_pivot = df_country_chart.pivot(index='国籍', columns='時点', values='人口').reset_index()
    df_country_pivot['増減数'] = df_country_pivot['2025/06'] - df_country_pivot['2024/06']
    df_country_pivot['増減率'] = (df_country_pivot['増減数'] / df_country_pivot['2024/06'] * 100).round(1)
    df_country_pivot = df_country_pivot.rename(columns={'2025/06': '人口'})

    # 総数を抽出してテーブル外に表示
    total_row = df_country_pivot[df_country_pivot['国籍'] == '総数'].iloc[0]
    total_pop = int(total_row['人口'])
    total_change = int(total_row['増減数'])
    total_rate = total_row['増減率']
    st.markdown(f'<p style="font-size:14px; margin-bottom:5px;"><b>総数:</b> {total_pop:,}人（{total_change:+,}, {total_rate:+.1f}%）</p>', unsafe_allow_html=True)

    # 総数を除外、固定順序で並べ替え
    df_country_pivot = df_country_pivot[df_country_pivot['国籍'] != '総数'].copy()
    # その他に集約
    df_country_pivot['国籍'] = df_country_pivot['国籍'].apply(lambda x: x if x in COUNTRY_ORDER else 'その他')
    df_country_pivot = df_country_pivot.groupby('国籍', as_index=False).agg({'人口': 'sum', '増減数': 'sum', '増減率': 'mean'})
    df_country_pivot['国籍'] = pd.Categorical(df_country_pivot['国籍'], categories=COUNTRY_ORDER[::-1], ordered=True)
    df_country_pivot = df_country_pivot.sort_values('国籍')

    # 指標切り替え
    metric_list = ['人口', '増減数', '増減率']
    selected_metric = st.segmented_control('指標', metric_list, default='人口',
                                            label_visibility='collapsed', key='country_metric_seg')
    if selected_metric is None:
        selected_metric = '人口'
    metric_options = {'人口': '人口', '増減数': '増減数', '増減率': '増減率（%）'}

    fig_country = px.bar(
        df_country_pivot, y='国籍', x=selected_metric, orientation='h',
        labels={'国籍': '', selected_metric: metric_options[selected_metric]},
        color_discrete_sequence=['#636EFA']
    )
    fig_country.update_layout(
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True, tickmode='linear', dtick=1),
        margin=dict(l=120, r=20, t=30, b=30), height=500,
        dragmode=False,
    )
    st.plotly_chart(fig_country, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False}, key='country_bar')
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 出入国在留管理庁 在留外国人統計（2025年6月）</p>', unsafe_allow_html=True)

    # 4. 在留資格別人口バーグラフ
    st.markdown(f'###### {selected_pref}の在留資格別人口と増減（前年比）')
    df_status_long = pd.read_csv(data_dir / 'zairyu_pref_status.csv')
    df_status_chart = df_status_long[df_status_long['都道府県'] == pref_filter].copy()

    # ピボットして2024/06と2025/06を横に並べる
    df_status_pivot = df_status_chart.pivot(index='在留資格', columns='時点', values='人口').reset_index()
    df_status_pivot['増減数'] = df_status_pivot['2025/06'] - df_status_pivot['2024/06']
    df_status_pivot['増減率'] = (df_status_pivot['増減数'] / df_status_pivot['2024/06'] * 100).round(1)
    df_status_pivot = df_status_pivot.rename(columns={'2025/06': '人口'})

    # 総数を抽出してグラフ外に表示
    total_status_row = df_status_pivot[df_status_pivot['在留資格'] == '総数'].iloc[0]
    total_status_pop = int(total_status_row['人口'])
    total_status_change = int(total_status_row['増減数'])
    total_status_rate = total_status_row['増減率']
    st.markdown(f'<p style="font-size:14px; margin-bottom:5px;"><b>総数:</b> {total_status_pop:,}人（{total_status_change:+,}, {total_status_rate:+.1f}%）</p>', unsafe_allow_html=True)

    # 総数を除外、固定順序で並べ替え（水平グラフ用に逆順）
    df_status_pivot = df_status_pivot[df_status_pivot['在留資格'] != '総数'].copy()
    df_status_pivot['在留資格'] = pd.Categorical(df_status_pivot['在留資格'], categories=STATUS_ORDER[::-1], ordered=True)
    df_status_pivot = df_status_pivot.sort_values('在留資格')

    # 指標切り替え
    status_metric_list = ['人口', '増減数', '増減率']
    selected_status_metric = st.segmented_control('在留資格指標', status_metric_list, default='人口',
                                                   label_visibility='collapsed', key='status_metric_seg')
    if selected_status_metric is None:
        selected_status_metric = '人口'
    status_metric_options = {'人口': '人口', '増減数': '増減数', '増減率': '増減率（%）'}

    fig_status = px.bar(
        df_status_pivot, y='在留資格', x=selected_status_metric, orientation='h',
        labels={'在留資格': '', selected_status_metric: status_metric_options[selected_status_metric]},
        color_discrete_sequence=['#00CC96']
    )
    fig_status.update_layout(
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True, tickmode='linear', dtick=1),
        margin=dict(l=160, r=20, t=30, b=30), height=350,
        dragmode=False,
    )
    st.plotly_chart(fig_status, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False}, key='status_bar')
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 出入国在留管理庁 在留外国人統計（2025年6月）</p>', unsafe_allow_html=True)
