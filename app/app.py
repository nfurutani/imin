import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title='外国人比率')

# 動的なスタイル調整
st.markdown("""
<style>
    /* フォントを見やすく */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500&display=swap');

    [data-testid="stDataFrame"] {
        font-family: 'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-size: 16px !important;
        -webkit-font-smoothing: antialiased !important;
    }

    /* カスタムテーブル */
    .custom-table {
        max-height: calc(100vh - 350px);
        overflow-y: auto;
        overflow-x: auto;
        margin-bottom: 1rem;
    }

    .custom-table table {
        width: 100%;
        border-collapse: collapse;
    }

    .custom-table th, .custom-table td {
        padding: 6px 8px;
        border-bottom: 1px solid #e0e0e0;
        white-space: nowrap;
        font-size: 14px;
    }

    .custom-table th {
        position: sticky;
        top: 0;
        background: #f0f2f6;
        font-weight: 500;
    }

    /* Bootstrapスタイルのタブ */
    [data-testid="stTabs"] [role="tablist"] {
        border-bottom: 1px solid #dee2e6 !important;
        gap: 0 !important;
    }

    [data-testid="stTabs"] button {
        color: #007bff !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 0.25rem 0.25rem 0 0 !important;
        padding: 0.5rem 1rem !important;
        margin-bottom: -1px !important;
    }

    [data-testid="stTabs"] button:hover {
        border-color: #e9ecef #e9ecef #dee2e6 !important;
    }

    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #495057 !important;
        font-weight: 500 !important;
        background: #fff !important;
        border-color: #dee2e6 #dee2e6 #fff !important;
    }

    /* モバイル（幅600px以下） */
    @media (max-width: 600px) {
        /* 上部の余白を削減 */
        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 0.5rem !important;
        }

        /* タイトル */
        h1 {
            font-size: 1.4rem !important;
            margin: 0 0 0.5rem 0 !important;
            padding: 0 !important;
        }

        /* セレクトボックスの余白削減 */
        [data-testid="stSelectbox"] {
            margin-bottom: 0.5rem !important;
        }

        /* テーブルの高さとフォント */
        .custom-table {
            height: calc(100vh - 280px) !important;
        }

        .custom-table th, .custom-table td {
            font-size: 12px !important;
            padding: 4px 6px !important;
        }

        /* フッター */
        .stMarkdown p, .stMarkdown a {
            font-size: 0.85rem !important;
        }

        hr {
            margin: 0.3rem 0 !important;
        }
    }

    /* モバイル横向き */
    @media (max-width: 900px) and (orientation: landscape) {
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0.3rem !important;
        }

        h1 {
            font-size: 1rem !important;
            margin: 0 0 0.3rem 0 !important;
        }

        [data-testid="stSelectbox"] {
            margin-bottom: 0.3rem !important;
        }

        .custom-table {
            height: calc(100vh - 180px) !important;
            min-height: 150px !important;
        }

        .stMarkdown p, .stMarkdown a {
            font-size: 0.75rem !important;
        }

        hr {
            margin: 0.2rem 0 !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# スクリプトの場所を基準にパスを解決
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'

df = pd.read_csv(DATA_DIR / 'daicho_city.csv')
df = df.rename(columns={'外国人人口':'外国人'})
df['比率'] = round(df['外国人'] / df['総人口'] * 100, 1)

st.title('外国人関係統計データ')
dev_mode = st.query_params.get('dev') == '1'
if dev_mode:
    tab3, tab1 = st.tabs(['外国人比率', '国籍・在留資格'])
else:
    tab3 = st.container()
    tab1 = None

if tab1 is not None:
  with tab1:
    df_zairyu = pd.read_csv(DATA_DIR / 'zairyu_country.csv')
    if df_zairyu['人口'].dtype == 'object':
        df_zairyu['人口'] = df_zairyu['人口'].str.replace(',', '').astype(float)

    # 地域フィルタ
    regions = ['アジア', 'ヨーロッパ', 'アフリカ', '北アメリカ', '南アメリカ', 'オセアニア', '無国籍']
    region_code_range = {
        'アジア': (1001, 1999), 'ヨーロッパ': (2001, 2999), 'アフリカ': (3001, 3999),
        '北アメリカ': (4001, 4999), '南アメリカ': (5001, 5999), 'オセアニア': (6001, 6999),
    }
    selected_region = st.selectbox('地域を選択', ['全地域'] + regions, label_visibility='collapsed', key='tab1_region')

    df_total = df_zairyu[df_zairyu['在留資格'] == '総数'].copy()

    # 集計時点をソートするためのキーを作成（例: "2023年12月" → 202312, "2023年6月" → 202306）
    def date_sort_key(s):
        import re
        m = re.match(r'(\d{4})年(\d+)月', s)
        return int(m.group(1)) * 100 + int(m.group(2)) if m else 0

    df_total['_sort_key'] = df_total['集計時点'].apply(date_sort_key)

    if selected_region == '全地域':
        st.markdown('##### 地域別 在留外国人の推移')
        df_chart_data = df_total[df_total['国籍・地域'].isin(regions)].copy()
        color_col = '国籍・地域'
    elif selected_region == '無国籍':
        st.markdown('##### 無国籍 在留外国人の推移')
        df_chart_data = df_total[df_total['国籍・地域'] == '無国籍'].copy()
        color_col = '国籍・地域'
    else:
        st.markdown(f'##### {selected_region} 国籍別 在留外国人の推移')
        lo, hi = region_code_range[selected_region]
        # 国籍名で絞り込み（cat02_codeは時期で変わるため、最新のコード体系から国籍名を取得）
        latest_tmp_key = df_total['_sort_key'].max()
        latest_tmp = df_total[df_total['_sort_key'] == latest_tmp_key]['集計時点'].iloc[0]
        country_names = df_total[
            (df_total['集計時点'] == latest_tmp) & (df_total['cat02_code'] >= lo) & (df_total['cat02_code'] <= hi)
        ]['国籍・地域'].unique().tolist()
        df_chart_data = df_total[df_total['国籍・地域'].isin(country_names)].copy()
        # 上位10カ国 + その他
        top_countries = (
            df_chart_data[df_chart_data['集計時点'] == latest_tmp]
            .sort_values('人口', ascending=False).head(8)['国籍・地域'].tolist()
        )
        df_chart_data['国籍・地域'] = df_chart_data['国籍・地域'].apply(
            lambda x: x if x in top_countries else 'その他'
        )
        df_chart_data = df_chart_data.groupby(['集計時点', '国籍・地域', '_sort_key'], as_index=False)['人口'].sum()
        color_col = '国籍・地域'

    # 時系列順にソート
    df_chart_data = df_chart_data.sort_values('_sort_key')
    latest_date = df_chart_data.loc[df_chart_data['_sort_key'].idxmax(), '集計時点']
    # X軸の正しい順序を確保
    date_order = df_chart_data.drop_duplicates('集計時点').sort_values('_sort_key')['集計時点'].tolist()

    # 人口順で凡例の順序を決定
    order_list = (
        df_chart_data[df_chart_data['集計時点'] == latest_date]
        .sort_values('人口', ascending=False)[color_col].tolist()
    )

    fig_line = px.line(
        df_chart_data, x='集計時点', y='人口', color=color_col,
        category_orders={color_col: order_list, '集計時点': date_order},
        markers=True, labels={'人口': '在留外国人数', '集計時点': ''}
    )

    fig_line.update_layout(
        xaxis_tickangle=-45, hovermode='x unified', height=450,
        margin=dict(l=40, r=20, t=50, b=30),
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='center', x=0.5),
    )
    st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 出入国在留管理庁 在留外国人統計</p>', unsafe_allow_html=True)

    # 人口ランキング
    st.markdown('##### 人口ランキング（直近）')
    df_rank_pop = df_chart_data[df_chart_data['集計時点'] == latest_date].sort_values('人口', ascending=False)
    df_rank_pop = df_rank_pop[[color_col, '人口']].reset_index(drop=True)
    df_rank_pop.index = df_rank_pop.index + 1
    df_rank_pop.index.name = '順位'
    st.dataframe(df_rank_pop.style.format({'人口': '{:,.0f}'}), use_container_width=True)

    # 増加率ランキング
    st.markdown('##### 増加率ランキング（2012年12月 → 直近）')
    oldest_date = '2012年12月'
    pivot = df_chart_data.pivot_table(index=color_col, columns='集計時点', values='人口', aggfunc='first').fillna(0)
    if oldest_date in pivot.columns and latest_date in pivot.columns:
        pivot['増加率(倍)'] = round(pivot[latest_date] / pivot[oldest_date].replace(0, 1), 1)
        pivot['増加数'] = (pivot[latest_date] - pivot[oldest_date]).astype(int)
        rank_table = pivot.sort_values('増加率(倍)', ascending=False)[['増加率(倍)', '増加数', oldest_date, latest_date]]
        rank_table = rank_table.rename(columns={oldest_date: '2012年12月', latest_date: '直近'})
        st.dataframe(rank_table.style.format({
            '増加率(倍)': '{:.1f}', '増加数': '{:,.0f}', '2012年12月': '{:,.0f}', '直近': '{:,.0f}'
        }), use_container_width=True)

with tab3:
    df_jinko = pd.read_csv(DATA_DIR / 'jinkosuikei.csv')

    st.markdown('##### 外国人比率推移')
    df_jinko['外国人人口（万人）'] = df_jinko['外国人人口'] / 10

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_jinko['時間軸'], y=df_jinko['外国人人口（万人）'],
        name='外国人人口（万人）', marker_color='#636EFA', yaxis='y', width=0.8,
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
    fig.update_layout(
        yaxis=dict(title='', showgrid=False),
        yaxis2=dict(title='', showgrid=False, overlaying='y', side='right',
                    range=[0, 4], dtick=1),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        margin=dict(l=40, r=40, t=30, b=30), height=320,
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 総務省統計局 人口推計</p>', unsafe_allow_html=True)

    # 市区町村別外国人比率テーブル
    st.markdown('##### 市区町村別外国人比率')
    pref_list3 = df[df['level'] == 'level1']['都道府県'].tolist()
    selected_pref3 = st.selectbox('都道府県を選択', ['全国'] + pref_list3, label_visibility='collapsed', key='tab3_pref')

    if selected_pref3 == '全国':
        df_display3 = df[df['level'] == 'level1'].sort_values('都道府県番号')
    else:
        df_display3 = df[(df['都道府県'] == selected_pref3) & (df['level'] == 'level3')]
        df_display3 = df_display3.sort_values('比率', ascending=False)

    display_cols = ['都道府県', '市区町村', '総人口', '外国人', '比率']
    df_styled3 = df_display3[display_cols].reset_index(drop=True)

    styled3 = df_styled3.style.format({
        '総人口': '{:,.0f}',
        '外国人': '{:,.0f}',
        '比率': '{:.1f}'
    }).background_gradient(
        subset=['総人口', '外国人', '比率'],
        cmap='Purples'
    ).set_properties(**{'text-align': 'center'}).set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'center')]},
        {'selector': 'td', 'props': [('text-align', 'center')]}
    ]).hide(axis='index')

    st.markdown(f'<div class="custom-table">{styled3.to_html()}</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 総務省 住民基本台帳に基づく人口（2025年1月）</p>', unsafe_allow_html=True)
