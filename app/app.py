import streamlit as st
import pandas as pd
from pathlib import Path

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
        height: calc(100vh - 350px);
        overflow-y: auto;
        overflow-x: auto;
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

df = pd.read_csv(DATA_DIR / 'streamlit.csv')
df = df.rename(columns={'外国人人口':'外国人'})
df['割合'] = round(df['外国人'] / df['総人口'] * 100, 1)

st.title('外国人人口割合')

# 都道府県の選択
pref_list = df[df['level'] == 'pref']['都道府県'].tolist()
selected_pref = st.selectbox('都道府県を選択', ['全国'] + pref_list)

if selected_pref == '全国':
    # 全国：都道府県一覧を表示（都道府県番号の昇順）
    df_display = df[df['level'] == 'pref'].sort_values('都道府県番号')
else:
    # 都道府県が選択された場合
    df_pref = df[df['都道府県'] == selected_pref]

    # 区がある市は除外し、代わりに区を表示
    cities_with_wards = df_pref[df_pref['level'] == 'ward']['parent_code'].unique()
    df_cities_without_wards = df_pref[(df_pref['level'] == 'city') & (~df_pref['index'].isin(cities_with_wards))]
    df_wards = df_pref[df_pref['level'] == 'ward']
    df_display = pd.concat([df_cities_without_wards, df_wards])

    # 割合で降順ソート
    df_display = df_display.sort_values('割合', ascending=False)

# 表示カラムを選択
display_cols = ['都道府県', '市区町村', '総人口', '外国人', '割合']
df_styled = df_display[display_cols].reset_index(drop=True)

# ヒートマップスタイルを適用
styled = df_styled.style.format({
    '総人口': '{:,.0f}',
    '外国人': '{:,.0f}',
    '割合': '{:.1f}'
}).background_gradient(
    subset=['総人口', '外国人', '割合'],
    cmap='Purples'
).set_properties(**{'text-align': 'center'}).set_table_styles([
    {'selector': 'th', 'props': [('text-align', 'center')]},
    {'selector': 'td', 'props': [('text-align', 'center')]}
]).hide(axis='index')

# HTMLテーブルとして表示（スクロール対応）
st.markdown(f"""
<div class="custom-table">
{styled.to_html()}
</div>
""", unsafe_allow_html=True)

# フッター
st.markdown('---')
st.markdown('Source: [総務省 住民基本台帳に基づく人口](https://www.soumu.go.jp/main_sosiki/jichi_gyousei/daityo/jinkou_jinkoudoutai-setaisuu.html)')
st.markdown('Data: 2025年1月')
