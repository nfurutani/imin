import streamlit as st
from pathlib import Path
import tab_jinkosuikei
import datetime

st.set_page_config(page_title='外国人比率')

# CSS読み込み
css_path = Path(__file__).parent / 'styles.css'
st.markdown(f'<style>{css_path.read_text()}</style>', unsafe_allow_html=True)

# データ読み込み
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'

# タブ切り替え
st.title('在留外国人統計')
tab1, tab2, tab3, tab4, tab5 = st.tabs(['都道府県別', '国籍別', '在留資格別', '特定技能・技能実習', 'ニュース'])

with tab1:
    tab_jinkosuikei.render_pref(DATA_DIR)

with tab2:
    tab_jinkosuikei.render_country(DATA_DIR)

with tab3:
    tab_jinkosuikei.render_status(DATA_DIR)

with tab4:
    tab_jinkosuikei.render_tokutei(DATA_DIR)

with tab5:
    st.markdown('##### 関連ニュース')
    news = [
        ( datetime.date.today(), '出入国在留管理庁', '特定技能に関する二国間の協力覚書',
         'https://www.jiji.com/jc/article?k=2025073001185&g=pol'),
        ('2025/07/30', '時事通信', '外国人比率、40年に10％超も　鈴木法相、近く推計公表',
         'https://www.jiji.com/jc/article?k=2025073001185&g=pol'),
        ('2025/10/26', '日本経済新聞', '想定ペースの2倍で増える外国人　なぜ円安下でも日本を目指すのか',
         'https://www.nikkei.com/article/DGXZQOUB21AQC0R21C25A0000000/'),
    ]
    for date, source, title, url in news:
        st.markdown(f'- **{date}**　[{title}]({url})（{source}）')
