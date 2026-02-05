import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import tab_zairyugaikokujin

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
    st.plotly_chart(fig, use_container_width=True, config={
        'displayModeBar': False, 'scrollZoom': False,
    })

    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 総務省統計局 人口推計</p>', unsafe_allow_html=True)

    # 在留外国人（フィルタ＋2チャート）
    tab_zairyugaikokujin.render(data_dir, key_prefix='zenkoku')


def render_pref(df, data_dir):
    """都道府県別タブ: 市区町村別外国人比率テーブル + 国籍別人口パイチャート"""
    st.markdown('##### 都道府県別 / 市区町村別')
    pref_list = df[df['level'] == 'level1']['都道府県'].tolist()
    selected_pref = st.selectbox('都道府県を選択', ['全国'] + pref_list, label_visibility='collapsed', key='tab_pref_select')

    st.markdown('###### 市区町村別外国人比率')

    if selected_pref == '全国':
        df_display = df[df['level'] == 'level1'].sort_values('比率', ascending=False)
    else:
        df_display = df[(df['都道府県'] == selected_pref) & (df['level'] == 'level3')]
        df_display = df_display.sort_values('比率', ascending=False)

    display_cols = ['都道府県', '市区町村', '総人口', '外国人', '比率']
    df_styled = df_display[display_cols].reset_index(drop=True)

    styled = df_styled.style.format({
        '総人口': '{:,.0f}',
        '外国人': '{:,.0f}',
        '比率': '{:.1f}'
    }).background_gradient(
        subset=['総人口', '外国人', '比率'],
        cmap='Purples'
    ).hide(axis='index')

    html = f'<div class="custom-table">{styled.to_html()}</div>'
    st.markdown(html, unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 総務省 住民基本台帳に基づく人口（2025年1月）</p>', unsafe_allow_html=True)

    # 国籍別人口（前年比）テーブル
    st.markdown('###### 国籍別人口（前年比）')
    df_country_long = pd.read_csv(data_dir / 'zairyu_pref_country.csv')
    pref_filter = '総数' if selected_pref == '全国' else selected_pref
    df_country_chart = df_country_long[df_country_long['都道府県'] == pref_filter].copy()

    # ピボットして2024/06と2025/06を横に並べる
    df_country_pivot = df_country_chart.pivot(index='国籍', columns='時点', values='人口').reset_index()
    df_country_pivot['増減数'] = df_country_pivot['2025/06'] - df_country_pivot['2024/06']
    df_country_pivot['増減率'] = (df_country_pivot['増減数'] / df_country_pivot['2024/06'] * 100).round(1)
    df_country_pivot = df_country_pivot.rename(columns={'2025/06': '人口（2025）'})
    df_country_pivot = df_country_pivot[['国籍', '人口（2025）', '増減数', '増減率']]

    # 総数を抽出してテーブル外に表示
    total_row = df_country_pivot[df_country_pivot['国籍'] == '総数'].iloc[0]
    total_pop = int(total_row['人口（2025）'])
    total_change = int(total_row['増減数'])
    total_rate = total_row['増減率']
    st.markdown(f'<p style="font-size:14px; margin-bottom:5px;"><b>総数:</b> {total_pop:,}人（{total_change:+,}, {total_rate:+.1f}%）</p>', unsafe_allow_html=True)

    # 総数を除外して増減数降順でソート
    df_country_pivot = df_country_pivot[df_country_pivot['国籍'] != '総数'].sort_values('増減数', ascending=False).reset_index(drop=True)

    styled_country_table = df_country_pivot.style.format({
        '人口（2025）': '{:,.0f}',
        '増減数': '{:+,.0f}',
        '増減率': '{:+.1f}%'
    }).background_gradient(
        subset=['人口（2025）', '増減数', '増減率'],
        cmap='Blues'
    ).hide(axis='index')

    html_country_table = f'<div class="custom-table">{styled_country_table.to_html()}</div>'
    st.markdown(html_country_table, unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 出入国在留管理庁 在留外国人統計（2025年6月）</p>', unsafe_allow_html=True)

    # 在留資格別人口（前年比）テーブル
    st.markdown('###### 在留資格別人口（前年比）')
    df_status_long = pd.read_csv(data_dir / 'zairyu_pref_status.csv')
    df_status_chart = df_status_long[df_status_long['都道府県'] == pref_filter].copy()

    # ピボットして2024/06と2025/06を横に並べる
    df_status_pivot = df_status_chart.pivot(index='在留資格', columns='時点', values='人口').reset_index()
    df_status_pivot['増減数'] = df_status_pivot['2025/06'] - df_status_pivot['2024/06']
    df_status_pivot['増減率'] = (df_status_pivot['増減数'] / df_status_pivot['2024/06'] * 100).round(1)
    df_status_pivot = df_status_pivot.rename(columns={'2025/06': '人口（2025）'})
    df_status_pivot = df_status_pivot[['在留資格', '人口（2025）', '増減数', '増減率']]

    # 総数を抽出してテーブル外に表示
    total_status_row = df_status_pivot[df_status_pivot['在留資格'] == '総数'].iloc[0]
    total_status_pop = int(total_status_row['人口（2025）'])
    total_status_change = int(total_status_row['増減数'])
    total_status_rate = total_status_row['増減率']
    st.markdown(f'<p style="font-size:14px; margin-bottom:5px;"><b>総数:</b> {total_status_pop:,}人（{total_status_change:+,}, {total_status_rate:+.1f}%）</p>', unsafe_allow_html=True)

    # 総数を除外して増減数降順でソート
    df_status_pivot = df_status_pivot[df_status_pivot['在留資格'] != '総数'].sort_values('増減数', ascending=False).reset_index(drop=True)

    styled_status_table = df_status_pivot.style.format({
        '人口（2025）': '{:,.0f}',
        '増減数': '{:+,.0f}',
        '増減率': '{:+.1f}%'
    }).background_gradient(
        subset=['人口（2025）', '増減数', '増減率'],
        cmap='BuGn'
    ).hide(axis='index')

    html_status_table = f'<div class="custom-table">{styled_status_table.to_html()}</div>'
    st.markdown(html_status_table, unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 出入国在留管理庁 在留外国人統計（2025年6月）</p>', unsafe_allow_html=True)

    # 国籍別・都道府県別人口（前年比）テーブル
    st.divider()
    st.markdown('##### 国籍別・都道府県別人口（前年比）')
    country_list = df_country_long['国籍'].unique().tolist()
    country_list = ['総数'] + [c for c in country_list if c != '総数']
    selected_country = st.selectbox('国籍を選択', country_list, label_visibility='collapsed', key='pref_country_filter')

    df_country_by_pref = df_country_long[df_country_long['国籍'] == selected_country].copy()
    df_country_by_pref = df_country_by_pref[~df_country_by_pref['都道府県'].str.contains('※', na=False)]
    df_country_by_pref = df_country_by_pref.groupby(['都道府県', '時点'], as_index=False)['人口'].sum()
    df_country_pref_pivot = df_country_by_pref.pivot(index='都道府県', columns='時点', values='人口').reset_index()
    df_country_pref_pivot['増減数'] = df_country_pref_pivot['2025/06'] - df_country_pref_pivot['2024/06']
    df_country_pref_pivot['増減率'] = (df_country_pref_pivot['増減数'] / df_country_pref_pivot['2024/06'] * 100).round(1)
    df_country_pref_pivot = df_country_pref_pivot.rename(columns={'2025/06': '人口（2025）'})
    df_country_pref_pivot = df_country_pref_pivot[['都道府県', '人口（2025）', '増減数', '増減率']]

    # 総数を抽出してテーブル外に表示
    total_pref_row = df_country_pref_pivot[df_country_pref_pivot['都道府県'] == '総数'].iloc[0]
    total_pref_pop = int(total_pref_row['人口（2025）'])
    total_pref_change = int(total_pref_row['増減数'])
    total_pref_rate = total_pref_row['増減率']
    st.markdown(f'<p style="font-size:14px; margin-bottom:5px;"><b>総数:</b> {total_pref_pop:,}人（{total_pref_change:+,}, {total_pref_rate:+.1f}%）</p>', unsafe_allow_html=True)

    # 総数を除外して増減数降順でソート
    df_country_pref_pivot = df_country_pref_pivot[df_country_pref_pivot['都道府県'] != '総数'].sort_values('増減数', ascending=False).reset_index(drop=True)

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

    # 在留資格別・都道府県別人口（前年比）テーブル
    st.divider()
    st.markdown('##### 在留資格別・都道府県別人口（前年比）')
    status_list = df_status_long['在留資格'].unique().tolist()
    status_list = ['総数'] + [s for s in status_list if s != '総数']
    selected_status = st.selectbox('在留資格を選択', status_list, label_visibility='collapsed', key='pref_status_filter')

    df_status_by_pref = df_status_long[df_status_long['在留資格'] == selected_status].copy()
    df_status_by_pref = df_status_by_pref[~df_status_by_pref['都道府県'].str.contains('※', na=False)]
    df_status_by_pref = df_status_by_pref.groupby(['都道府県', '時点'], as_index=False)['人口'].sum()
    df_status_pref_pivot = df_status_by_pref.pivot(index='都道府県', columns='時点', values='人口').reset_index()
    df_status_pref_pivot['増減数'] = df_status_pref_pivot['2025/06'] - df_status_pref_pivot['2024/06']
    df_status_pref_pivot['増減率'] = (df_status_pref_pivot['増減数'] / df_status_pref_pivot['2024/06'] * 100).round(1)
    df_status_pref_pivot = df_status_pref_pivot.rename(columns={'2025/06': '人口（2025）'})
    df_status_pref_pivot = df_status_pref_pivot[['都道府県', '人口（2025）', '増減数', '増減率']]

    # 総数を抽出してテーブル外に表示
    total_status_pref_row = df_status_pref_pivot[df_status_pref_pivot['都道府県'] == '総数'].iloc[0]
    total_status_pref_pop = int(total_status_pref_row['人口（2025）'])
    total_status_pref_change = int(total_status_pref_row['増減数'])
    total_status_pref_rate = total_status_pref_row['増減率']
    st.markdown(f'<p style="font-size:14px; margin-bottom:5px;"><b>総数:</b> {total_status_pref_pop:,}人（{total_status_pref_change:+,}, {total_status_pref_rate:+.1f}%）</p>', unsafe_allow_html=True)

    # 総数を除外して増減数降順でソート
    df_status_pref_pivot = df_status_pref_pivot[df_status_pref_pivot['都道府県'] != '総数'].sort_values('増減数', ascending=False).reset_index(drop=True)

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
