import re
import streamlit as st
import pandas as pd
import plotly.express as px


def _date_sort_key(s):
    m = re.match(r'(\d{4})年(\d+)月', s)
    return int(m.group(1)) * 100 + int(m.group(2)) if m else 0


def render(data_dir):
    df_zairyu = pd.read_csv(data_dir / 'zairyu_country.csv')
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
    df_total['_sort_key'] = df_total['集計時点'].apply(_date_sort_key)

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
        latest_tmp_key = df_total['_sort_key'].max()
        latest_tmp = df_total[df_total['_sort_key'] == latest_tmp_key]['集計時点'].iloc[0]
        country_names = df_total[
            (df_total['集計時点'] == latest_tmp) & (df_total['cat02_code'] >= lo) & (df_total['cat02_code'] <= hi)
        ]['国籍・地域'].unique().tolist()
        df_chart_data = df_total[df_total['国籍・地域'].isin(country_names)].copy()
        # 上位8カ国 + その他
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
