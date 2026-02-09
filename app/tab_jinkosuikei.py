import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import tab_zairyugaikokujin

COUNTRY_ORDER = ['中国', 'ベトナム', '韓国', 'フィリピン', 'ネパール', 'インドネシア', 'ブラジル',
                 'ミャンマー', 'スリランカ', '台湾', '米国', 'タイ', 'インド', 'ペルー', 'バングラデシュ',
                 'パキスタン', 'カンボジア', '朝鮮', 'モンゴル', '英国', 'その他']

STATUS_ORDER = ['永住者', '技術・人文知識・国際業務', '技能実習', '留学', '特定技能', '家族滞在',
                '定住者', '日本人の配偶者等', '特定活動', '特別永住者', 'その他']

def render(data_dir):
    df_jinko = pd.read_csv(data_dir / 'jinkosuikei.csv')

    st.markdown('##### 外国人数・比率推移')
    df_jinko['外国人人口（万人）'] = df_jinko['外国人人口'] / 10

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_jinko['時間軸'], y=df_jinko['外国人人口（万人）'],
        name='外国人数（万人）', marker_color='#636EFA', yaxis='y', width=0.8,
    ))
    fig.add_trace(go.Scatter(
        x=df_jinko['時間軸'], y=df_jinko['外国人比率'],
        name='外国人比率（%）', mode='lines+markers',
        line=dict(color='#EF553B', width=2), marker=dict(size=5), yaxis='y2',
    ))
    fig.add_vline(x='2012年', line_dash='dash', line_color='gray', line_width=1)
    fig.add_annotation(x='2012年', xshift=-10, y=.9, yref='paper',
                       text='第2次安倍内閣', showarrow=False,
                       font=dict(size=10, color='blue'), textangle=-90, yanchor='top')
    
    # グラフの表示幅の改善:
    # Plotlyにはデフォルトでautomargin=Trueが設定されており、
    # Y軸のtickラベル（「100」「200」「300」や右側の「1」「2」「3」「4」）が収まるように、
    # margin=dict(l=0, r=0)と指定しても自動的にマージンが追加されます。
    # つまりl=0, r=0の指定がPlotlyのautomargin機能に上書きされている状態です。

    # 対処方法:
    # yaxis=dict(..., automargin=False)とyaxis2=dict(..., automargin=False)を追加すれば、
    # 強制的にマージン0になります。ただしtickラベルが切れます
    # tickラベルをチャート内側に表示するticklabelposition='inside'を使えば、
    # ラベルを保ちつつマージンを削減できます
    # ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
    
    fig.update_layout(
        yaxis=dict(title='', showgrid=False, automargin=False, fixedrange=True, dtick=100,
                   range=[0, df_jinko['外国人人口（万人）'].max() * 1.1]),
        yaxis2=dict(title='', showgrid=False, overlaying='y', side='right',
                    range=[0, 4], dtick=1, automargin=False, fixedrange=True,
                    ticksuffix='%'),
        xaxis=dict(fixedrange=True),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5,
                    itemclick=False, itemdoubleclick=False),
        margin=dict(l=30, r=30, t=30, b=30), height=320,
        dragmode=False,
    )
    # st.plotly_chart(fig, use_container_width=True, config={
    #     'displayModeBar': False, 'scrollZoom': False,
    # })

    # 修正案：ユニークなキーを追加
    st.plotly_chart(fig, use_container_width=True, key="national_main_chart", config={
        'displayModeBar': False, 'scrollZoom': False,
    })

    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 総務省統計局 人口推計</p>', unsafe_allow_html=True)


def render_pref(data_dir):
    """都道府県別タブ: 外国人数推移 + 都道府県別比率 + 国籍別・在留資格別グラフ"""
    st.markdown('##### 都道府県別 / 市区町村別')
    # 都道府県リストをparquetから取得
    df_daicho_all = pd.read_parquet(data_dir / 'parquet' / 'estat_daicho.parquet')
    pref_list = sorted(df_daicho_all['都道府県名'].unique().tolist())
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
        yaxis=dict(title='', showgrid=False, fixedrange=True),
        yaxis2=dict(title='', showgrid=False, overlaying='y', side='right', fixedrange=True, ticksuffix='%'),
        xaxis=dict(fixedrange=True, dtick=1),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5,
                    itemclick=False, itemdoubleclick=False),
        margin=dict(l=50, r=50, t=30, b=30), height=320,
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
    sort_options = ['総人口', '外国人', '比率', '前年比']
    selected_sort = st.segmented_control('ソート順', sort_options, default='比率',
                                          label_visibility='collapsed', key='pref_table_sort_seg')
    if selected_sort is None:
        selected_sort = '比率'
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


def render_country(data_dir):
    """国籍別タブ: フィルター + グラフ + 都道府県別テーブル"""
    # フィルター（一番上）
    df_country_long = pd.read_csv(data_dir / 'zairyu_pref_country.csv')
    country_list = df_country_long['国籍'].unique().tolist()
    country_list = ['すべての国籍'] + [c for c in country_list if c != '総数']
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
    sort_metric_list = ['人口', '増減数', '増減率']
    selected_sort_metric = st.segmented_control('ソート順', sort_metric_list, default='人口',
                                                  label_visibility='collapsed', key='country_pref_sort_seg')
    if selected_sort_metric is None:
        selected_sort_metric = '人口'
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


def render_status(data_dir):
    """在留資格別タブ: フィルター + グラフ + 都道府県別テーブル"""
    # フィルター（一番上）
    df_status_long = pd.read_csv(data_dir / 'zairyu_pref_status.csv')
    status_list = df_status_long['在留資格'].unique().tolist()
    status_list = ['すべての在留資格'] + [s for s in status_list if s != '総数']
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
        '技能実習': '特定技能・技能実習',
        '特定技能': '特定技能・技能実習',
        '日本人の配偶者等': '配偶者等',
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


def render_tokutei(data_dir):
    """特定技能・技能実習タブ: 特定技能・技能実習の推移"""
    st.markdown('##### 特定技能・技能実習の推移')
    st.markdown('2028年の目標値123万人に向けた推計を含む')

    df_zairyu = pd.read_csv(data_dir / 'zairyu_country.csv')
    if df_zairyu['人口'].dtype == 'object':
        df_zairyu['人口'] = df_zairyu['人口'].str.replace(',', '').astype(float)

    # 技能実習の個別資格（2013年〜2023年用）
    gino_visas = ['技能実習１号イ', '技能実習１号ロ', '技能実習２号イ', '技能実習２号ロ', '技能実習３号イ', '技能実習３号ロ']
    # 特定技能の個別資格（2019年〜2023年用）
    tokutei_visas = ['特定技能１号', '特定技能２号']

    # 個別在留資格のデータを抽出（2013〜2023年用）
    df_individual = df_zairyu[
        (df_zairyu['在留資格'].isin(gino_visas + tokutei_visas)) &
        (df_zairyu['国籍・地域'] == '総数')
    ].copy()

    # 合計カテゴリのデータ（2024〜2025年用）
    df_total = df_zairyu[
        (df_zairyu['在留資格'].isin(['特定技能合計', '技能実習合計'])) &
        (df_zairyu['国籍・地域'] == '総数')
    ].copy()

    # 集計時点ごとに合算
    df_individual_sum = df_individual.groupby('集計時点', as_index=False)['人口'].sum()
    df_total_sum = df_total.groupby('集計時点', as_index=False)['人口'].sum()

    # 2024年以降は合計カテゴリを使用、それ以外は個別資格の合算を使用
    df_chart = pd.concat([
        df_individual_sum[~df_individual_sum['集計時点'].str.contains('2024|2025')],
        df_total_sum[df_total_sum['集計時点'] == '2024年12月']
    ], ignore_index=True)

    # 2024年12月のデータから2028年の目標値まで補間
    total_2024 = df_chart[df_chart['集計時点'] == '2024年12月']['人口'].values[0]

    # 2028年目標: 123万人
    total_2028 = 1230000

    # 線形補間で2025, 2026, 2027を計算
    total_2025 = total_2024 + (total_2028 - total_2024) / 4
    total_2026 = total_2024 + (total_2028 - total_2024) * 2 / 4
    total_2027 = total_2024 + (total_2028 - total_2024) * 3 / 4

    # 将来データを追加
    future_data = [
        {'集計時点': '2025年12月', '人口': total_2025},
        {'集計時点': '2026年12月', '人口': total_2026},
        {'集計時点': '2027年12月', '人口': total_2027},
        {'集計時点': '2028年12月', '人口': total_2028},
    ]
    df_future = pd.DataFrame(future_data)
    df_chart = pd.concat([df_chart, df_future], ignore_index=True)

    # 時系列ソート用のキーを付与
    import re
    def date_sort_key(s):
        m = re.match(r'(\d{4})年(\d+)月', s)
        return int(m.group(1)) * 100 + int(m.group(2)) if m else 0

    df_chart['_sort_key'] = df_chart['集計時点'].apply(date_sort_key)
    df_chart = df_chart.sort_values('_sort_key')

    # 横軸ラベルから「12月」を削除
    df_chart['年'] = df_chart['集計時点'].str.replace('12月', '')

    # 実績と推計を分割
    df_actual = df_chart[~df_chart['集計時点'].str.contains('2025|2026|2027|2028')].copy()
    df_projected = df_chart[df_chart['集計時点'].str.contains('2024|2025|2026|2027|2028')].copy()

    fig = go.Figure()

    # 実績（実線）
    fig.add_trace(go.Scatter(
        x=df_actual['年'], y=df_actual['人口'],
        mode='lines+markers+text',
        name='実績',
        line=dict(color='#636EFA', width=2),
        marker=dict(size=8),
        text=df_actual['人口'].apply(lambda x: f'{x/10000:.1f}万'),
        textposition='top center',
        textfont=dict(size=10),
    ))

    # 推計（点線）- 2024年はマーカーなし（実績と重複するため）
    projected_marker_sizes = [0] + [8] * (len(df_projected) - 1)  # 2024年は0、それ以降は8
    projected_texts = [''] + [f'{x/10000:.1f}万' for x in df_projected['人口'].iloc[1:]]  # 2024年はラベルなし
    fig.add_trace(go.Scatter(
        x=df_projected['年'], y=df_projected['人口'],
        mode='lines+markers+text',
        name='推計',
        line=dict(color='#FFA15A', width=2, dash='dash'),
        marker=dict(size=projected_marker_sizes),
        text=projected_texts,
        textposition='top center',
        textfont=dict(size=10),
    ))

    fig.update_layout(
        xaxis=dict(tickangle=-45, fixedrange=True, categoryorder='array', categoryarray=df_chart['年'].tolist()),
        yaxis=dict(fixedrange=True, title='在留外国人数'),
        hovermode='x unified', height=450,
        margin=dict(l=40, r=20, t=50, b=30),
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='center', x=0.5),
        dragmode=False,
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False}, key='tokutei_chart')
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 出入国在留管理庁 在留外国人統計 / 2025年以降は推計値</p>', unsafe_allow_html=True)
