import streamlit as st
import pandas as pd
from pathlib import Path
import tab_jinkosuikei
import tab_zairyugaikokujin

st.set_page_config(page_title='外国人比率')

# CSS読み込み
css_path = Path(__file__).parent / 'styles.css'
st.markdown(f'<style>{css_path.read_text()}</style>', unsafe_allow_html=True)

# データ読み込み
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'

df = pd.read_csv(DATA_DIR / 'daicho_city.csv')
df = df.rename(columns={'外国人人口': '外国人'})
df['比率'] = round(df['外国人'] / df['総人口'] * 100, 1)

# タブ切り替え
st.title('外国人関係統計データ')
dev_mode = st.query_params.get('dev') == '1'
if dev_mode:
    tab3, tab1 = st.tabs(['外国人比率', '国籍・在留資格'])
else:
    tab3 = st.container()
    tab1 = None

if tab1 is not None:
    with tab1:
        tab_zairyugaikokujin.render(DATA_DIR)

with tab3:
    tab_jinkosuikei.render(DATA_DIR, df)
