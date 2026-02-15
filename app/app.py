import streamlit as st

st.set_page_config(page_title='OpenJP')
st.logo('app/logo.svg')

pg = st.navigation([
    st.Page("page_imin.py", title="在留外国人"),
    st.Page("page_megasolar.py", title="メガソーラー"),
])
pg.run()
