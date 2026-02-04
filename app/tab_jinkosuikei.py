import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render(data_dir, df):
    df_jinko = pd.read_csv(data_dir / 'jinkosuikei.csv')

    st.markdown('##### 外国人比率推移')
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
                    range=[0, 4], dtick=1, automargin=False, fixedrange=True),
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

    # 市区町村別外国人比率テーブル
    st.markdown('##### 市区町村別外国人比率')
    pref_list = df[df['level'] == 'level1']['都道府県'].tolist()
    selected_pref = st.selectbox('都道府県を選択', ['全国'] + pref_list, label_visibility='collapsed', key='tab3_pref')

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
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 総務省 住民基本台帳に基づく人口（2025年1月）</p>', unsafe_allow_html=True)
