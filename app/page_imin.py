import streamlit as st
from pathlib import Path
import tab_pref
import tab_country
import tab_status
import tab_tokutei
import datetime

# CSS読み込み
css_path = Path(__file__).parent / 'styles.css'
st.markdown(f'<style>{css_path.read_text()}</style>', unsafe_allow_html=True)

# データ読み込み
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'

# タブ切り替え
st.title('在留外国人')
tab1, tab2, tab3, tab4 = st.tabs(['都道府県別', '国籍別', '在留資格別', 'ニュース'])

with tab1:
    tab_pref.render(DATA_DIR)

with tab2:
    tab_country.render(DATA_DIR)

with tab3:
    tab_status.render(DATA_DIR)

# with tab_tokutei:
#     tab_tokutei.render(DATA_DIR)

with tab4:
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
