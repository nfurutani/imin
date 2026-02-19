import streamlit as st

st.set_page_config(page_title='OpenJP')
st.logo('app/logo.svg')

pg = st.navigation([
    st.Page("page_megasolar.py", title="メガソーラー"),
    st.Page("page_imin.py", title="在留外国人"),
    st.Page("page_jinko.py", title="人口減少"),
    st.Page("page_zaisei.py", title="財政力指数"),
])
pg.run()
