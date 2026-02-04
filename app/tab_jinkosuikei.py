import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
    pref_list = df[df['level'] == 'level1']['都道府県'].tolist()
    selected_pref = st.selectbox('都道府県を選択', ['全国'] + pref_list, label_visibility='collapsed', key='tab_pref_select')

    st.markdown('##### 市区町村別外国人比率')

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

    # 国籍別人口パイチャート
    st.divider()
    st.markdown('##### 国籍別人口（2025年6月）')
    df_zairyu_pref = pd.read_csv(data_dir / 'zairyu_pref.csv')

    if selected_pref == '全国':
        df_pie = df_zairyu_pref.groupby('国籍', as_index=False)['人口_2025'].sum()
    else:
        df_pie = df_zairyu_pref[df_zairyu_pref['都道府県'] == selected_pref].copy()

    # 上位10カ国 + その他
    df_pie = df_pie.sort_values('人口_2025', ascending=False)
    top10 = df_pie.head(10)
    others = df_pie.iloc[10:]
    if len(others) > 0:
        others_row = pd.DataFrame({'国籍': ['その他'], '人口_2025': [others['人口_2025'].sum()]})
        df_pie = pd.concat([top10, others_row], ignore_index=True)
    else:
        df_pie = top10

    total_pop = int(df_pie['人口_2025'].sum())
    pastel_colors = [
        '#A8D8EA', '#AA96DA', '#FCBAD3', '#FFFFD2', '#B5EAD7',
        '#FFB7B2', '#E2F0CB', '#C7CEEA', '#FFDAC1', '#F0E6EF', '#D4E4ED'
    ]
    fig_pie = px.pie(
        df_pie, values='人口_2025', names='国籍',
        hole=0.5, color_discrete_sequence=pastel_colors,
    )
    fig_pie.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        height=500,
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5),
        annotations=[dict(
            text=f'{total_pop:,}<br>人',
            x=0.5, y=0.5, font_size=32, showarrow=False
        )],
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label+value')
    st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 出入国在留管理庁 在留外国人統計</p>', unsafe_allow_html=True)

    # 国籍別・都道府県別人口テーブル
    st.divider()
    st.markdown('##### 国籍別・都道府県別人口（2025年6月）')
    region_list = ['全地域'] + df_zairyu_pref['地域'].dropna().unique().tolist()
    col1, col2 = st.columns(2)
    with col1:
        selected_region_filter = st.selectbox('地域', region_list, label_visibility='collapsed', key='tab_pref_region')
    with col2:
        if selected_region_filter == '全地域':
            df_filtered = df_zairyu_pref
        else:
            df_filtered = df_zairyu_pref[df_zairyu_pref['地域'] == selected_region_filter]
        country_list = ['全国籍'] + sorted(df_filtered['国籍'].unique().tolist())
        selected_country = st.selectbox('国籍', country_list, label_visibility='collapsed', key='tab_pref_country')

    if selected_country == '全国籍':
        df_country = df_filtered.groupby('都道府県', as_index=False)['人口_2025'].sum()
    else:
        df_country = df_filtered[df_filtered['国籍'] == selected_country].copy()
        df_country = df_country[['都道府県', '人口_2025']]
    df_country = df_country.sort_values('人口_2025', ascending=False)
    df_country = df_country.rename(columns={'人口_2025': '人口'})
    df_country = df_country.reset_index(drop=True)

    styled_country = df_country.style.format({
        '人口': '{:,.0f}'
    }).background_gradient(
        subset=['人口'],
        cmap='Blues'
    ).hide(axis='index')

    html_country = f'<div class="custom-table">{styled_country.to_html()}</div>'
    st.markdown(html_country, unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 出入国在留管理庁 在留外国人統計</p>', unsafe_allow_html=True)
