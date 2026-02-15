import re
import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render(data_dir):
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
