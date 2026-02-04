import re
import streamlit as st
import pandas as pd
import plotly.express as px

CATEGORY_MAP = {
    '特別永住者': '特別永住者',
    '永住者': '永住者',
    '永住者の配偶者等': '配偶者等',
    '日本人の配偶者等': '配偶者等',
    '家族滞在': '家族滞在',
    '定住者': '定住者',
    '特定技能１号': '特定技能・技能実習',
    '特定技能２号': '特定技能・技能実習',
    '技能実習１号イ': '特定技能・技能実習',
    '技能実習１号ロ': '特定技能・技能実習',
    '技能実習２号イ': '特定技能・技能実習',
    '技能実習２号ロ': '特定技能・技能実習',
    '技能実習３号イ': '特定技能・技能実習',
    '技能実習３号ロ': '特定技能・技能実習',
    '留学': '留学',
    '特定活動': '特定活動',
    '技術・人文知識・国際業務': '技術・人文知識・国際業務',
    '技術': '技術・人文知識・国際業務',
    '人文知識・国際業務': '技術・人文知識・国際業務',
    '技能': 'その他', '経営・管理': 'その他', '投資・経営': 'その他',
    '高度専門職１号イ': 'その他', '高度専門職１号ロ': 'その他',
    '高度専門職１号ハ': 'その他', '高度専門職２号': 'その他',
    '教育': 'その他', '教授': 'その他', '宗教': 'その他', '医療': 'その他',
    '興行': 'その他', '介護': 'その他', '研究': 'その他',
    '文化活動': 'その他', '芸術': 'その他', '報道': 'その他',
    '研修': 'その他', '法律・会計業務': 'その他',
}

REGIONS = ['アジア', 'ヨーロッパ', 'アフリカ', '北アメリカ', '南アメリカ', 'オセアニア', '無国籍']
REGION_CODE_RANGE = {
    'アジア': (1001, 1999), 'ヨーロッパ': (2001, 2999), 'アフリカ': (3001, 3999),
    '北アメリカ': (4001, 4999), '南アメリカ': (5001, 5999), 'オセアニア': (6001, 6999),
}

VISA_GROUPS = ['全在留資格'] + sorted(set(CATEGORY_MAP.values()))


def _date_sort_key(s):
    m = re.match(r'(\d{4})年(\d+)月', s)
    return int(m.group(1)) * 100 + int(m.group(2)) if m else 0


def _get_country_names(df_total, selected_region, latest_date):
    """地域に応じた国籍リストを返す"""
    if selected_region == '全地域':
        return []
    if selected_region == '無国籍':
        return []
    lo, hi = REGION_CODE_RANGE[selected_region]
    names = df_total[
        (df_total['集計時点'] == latest_date) & (df_total['cat02_code'] >= lo) & (df_total['cat02_code'] <= hi)
    ]['国籍・地域'].unique().tolist()
    return sorted(names)


def _filter_by_visa(df, selected_visa):
    """在留資格フィルタを適用。'全在留資格'なら在留資格=総数、それ以外はグループに含まれる個別資格を合算"""
    if selected_visa == '全在留資格':
        return df[df['在留資格'] == '総数'].copy()
    visa_keys = [k for k, v in CATEGORY_MAP.items() if v == selected_visa]
    return df[df['在留資格'].isin(visa_keys)].copy()


def render(data_dir, key_prefix='tab1'):
    df_zairyu = pd.read_csv(data_dir / 'zairyu_country.csv')
    if df_zairyu['人口'].dtype == 'object':
        df_zairyu['人口'] = df_zairyu['人口'].str.replace(',', '').astype(float)

    # ソートキー付与
    df_zairyu['_sort_key'] = df_zairyu['集計時点'].apply(_date_sort_key)
    latest_sort_key = df_zairyu['_sort_key'].max()
    latest_date = df_zairyu[df_zairyu['_sort_key'] == latest_sort_key]['集計時点'].iloc[0]

    # --- フィルタ ---
    st.divider()
    st.markdown('##### 地域・国籍別 / 在留資格別')
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_region = st.selectbox('地域', ['全地域'] + REGIONS, label_visibility='collapsed', key=f'{key_prefix}_region')
    with col2:
        # 地域に応じた国籍リスト
        df_total_tmp = df_zairyu[df_zairyu['在留資格'] == '総数']
        country_names = _get_country_names(df_total_tmp, selected_region, latest_date)
        if country_names:
            selected_country = st.selectbox('国籍', ['全国籍'] + country_names, label_visibility='collapsed', key=f'{key_prefix}_country')
        else:
            selected_country = '全国籍'
            st.selectbox('国籍', ['全国籍'], label_visibility='collapsed', key=f'{key_prefix}_country', disabled=True)
    with col3:
        selected_visa = st.selectbox('在留資格', VISA_GROUPS, label_visibility='collapsed', key=f'{key_prefix}_visa')

    # --- チャート1: 国籍・地域別推移 ---
    df_filtered = _filter_by_visa(df_zairyu, selected_visa)
    # 在留資格フィルタで個別資格を選んだ場合、国籍・地域ごとに合算
    if selected_visa != '全在留資格':
        df_filtered = df_filtered.groupby(
            ['集計時点', '国籍・地域', 'cat02_code', '_sort_key'], as_index=False
        )['人口'].sum()

    visa_label = f'（{selected_visa}）' if selected_visa != '全在留資格' else ''

    if selected_country != '全国籍':
        st.markdown(f'###### {selected_country} 在留外国人の推移{visa_label}')
        df_chart_data = df_filtered[df_filtered['国籍・地域'] == selected_country].copy()
        color_col = '国籍・地域'
    elif selected_region == '全地域':
        st.markdown(f'###### 地域別 在留外国人の推移{visa_label}')
        df_chart_data = df_filtered[df_filtered['国籍・地域'].isin(REGIONS)].copy()
        color_col = '国籍・地域'
    elif selected_region == '無国籍':
        st.markdown('###### 無国籍 在留外国人の推移')
        df_chart_data = df_filtered[df_filtered['国籍・地域'] == '無国籍'].copy()
        color_col = '国籍・地域'
    else:
        st.markdown(f'###### {selected_region} 国籍別 在留外国人の推移{visa_label}')
        lo, hi = REGION_CODE_RANGE[selected_region]
        names = df_filtered[
            (df_filtered['集計時点'] == latest_date) & (df_filtered['cat02_code'] >= lo) & (df_filtered['cat02_code'] <= hi)
        ]['国籍・地域'].unique().tolist()
        df_chart_data = df_filtered[df_filtered['国籍・地域'].isin(names)].copy()
        # 上位8カ国 + その他
        top_countries = (
            df_chart_data[df_chart_data['集計時点'] == latest_date]
            .sort_values('人口', ascending=False).head(9)['国籍・地域'].tolist()
        )
        df_chart_data['国籍・地域'] = df_chart_data['国籍・地域'].apply(
            lambda x: x if x in top_countries else 'その他'
        )
        df_chart_data = df_chart_data.groupby(['集計時点', '国籍・地域', '_sort_key'], as_index=False)['人口'].sum()
        color_col = '国籍・地域'

    df_chart_data = df_chart_data.sort_values('_sort_key')
    if len(df_chart_data) > 0:
        chart_latest = df_chart_data.loc[df_chart_data['_sort_key'].idxmax(), '集計時点']
        date_order = df_chart_data.drop_duplicates('集計時点').sort_values('_sort_key')['集計時点'].tolist()
        order_list = (
            df_chart_data[df_chart_data['集計時点'] == chart_latest]
            .sort_values('人口', ascending=False)[color_col].tolist()
        )
        fig1 = px.line(
            df_chart_data, x='集計時点', y='人口', color=color_col,
            category_orders={color_col: order_list, '集計時点': date_order},
            labels={'人口': '在留外国人数', '集計時点': ''}
        )
        fig1.update_traces(mode='lines+markers')
        fig1.update_layout(
            xaxis=dict(tickangle=-45, fixedrange=True),
            yaxis=dict(fixedrange=True),
            hovermode='x unified', height=450,
            margin=dict(l=40, r=20, t=50, b=30),
            template='plotly_white',
            legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='center', x=0.5),
            dragmode=False,
        )
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False}, key=f'{key_prefix}_chart1')
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 出入国在留管理庁 在留外国人統計</p>', unsafe_allow_html=True)

    # --- チャート2: 在留資格グループ別推移 ---
    filter_label = ''
    if selected_country != '全国籍':
        df_visa = df_zairyu[df_zairyu['国籍・地域'] == selected_country].copy()
        filter_label = f'（{selected_country}）'
    elif selected_region != '全地域' and selected_region != '無国籍':
        lo, hi = REGION_CODE_RANGE[selected_region]
        df_visa = df_zairyu[
            (df_zairyu['cat02_code'] >= lo) & (df_zairyu['cat02_code'] <= hi)
        ].copy()
        filter_label = f'（{selected_region}）'
    elif selected_region == '無国籍':
        df_visa = df_zairyu[df_zairyu['国籍・地域'] == '無国籍'].copy()
        filter_label = '（無国籍）'
    else:
        df_visa = df_zairyu[df_zairyu['国籍・地域'] == '総数'].copy()

    if selected_visa != '全在留資格':
        filter_label += f'（{selected_visa}）' if filter_label else f'（{selected_visa}）'
    st.markdown(f'###### 在留資格グループ別の推移{filter_label}')
    df_visa = df_visa[df_visa['在留資格'].isin(CATEGORY_MAP.keys())]
    df_visa['在留資格グループ'] = df_visa['在留資格'].map(CATEGORY_MAP)
    if selected_visa != '全在留資格':
        df_visa = df_visa[df_visa['在留資格グループ'] == selected_visa]
    df_visa = df_visa.groupby(['集計時点', '在留資格グループ', '_sort_key'], as_index=False)['人口'].sum()
    df_visa = df_visa.sort_values('_sort_key')

    if len(df_visa) > 0:
        visa_latest = df_visa.loc[df_visa['_sort_key'].idxmax(), '集計時点']
        visa_date_order = df_visa.drop_duplicates('集計時点').sort_values('_sort_key')['集計時点'].tolist()
        visa_order = (
            df_visa[df_visa['集計時点'] == visa_latest]
            .sort_values('人口', ascending=False)['在留資格グループ'].tolist()
        )
        fig_bar2 = px.bar(
            df_visa, x='集計時点', y='人口', color='在留資格グループ',
            category_orders={'在留資格グループ': visa_order, '集計時点': visa_date_order},
            labels={'人口': '在留外国人数', '集計時点': ''}
        )
        fig_bar2.update_layout(
            barmode='stack',
            xaxis=dict(tickangle=-45, fixedrange=True),
            yaxis=dict(fixedrange=True),
            hovermode='x unified', height=450,
            margin=dict(l=40, r=20, t=50, b=30),
            template='plotly_white',
            legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='center', x=0.5),
            dragmode=False,
        )
        st.plotly_chart(fig_bar2, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False}, key=f'{key_prefix}_chart2')
    st.markdown('<p style="font-size:12px; color:gray; margin-top:-10px;">Source: 出入国在留管理庁 在留外国人統計</p>', unsafe_allow_html=True)
