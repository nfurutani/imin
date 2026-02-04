import pandas as pd
from pathlib import Path

# スクリプトの場所を基準にパスを解決
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'/'zairyu'

file1 = DATA_DIR / 'FEH_00250012_260131110539.csv'
file2 = DATA_DIR / 'FEH_00250012_260131110545.csv'
file3 = DATA_DIR / 'FEH_00250012_260203200255.csv'
df1 = pd.read_csv(file1,encoding='shift_jis')
df2 = pd.read_csv(file2,encoding='shift_jis')
df3 = pd.read_csv(file3,encoding='shift_jis')

#######################################
# df1,df2の準備
#######################################
df = pd.concat([df1, df2])
# df = df[['在留資格','国籍・地域','集計時点（半期毎）','unit','value']]

# df側の表記を df3 に合わせる例
replace_dict ={
    '韓国':'韓国・朝鮮',
    '朝鮮':'韓国・朝鮮',
    }

df['国籍・地域'] = df['国籍・地域'].replace(replace_dict)

# df側の表記を df3 に合わせる例
replace_dict ={
    1110:1130, #韓国・朝鮮
    1120:1130, #韓国・朝鮮
    }
df['cat02_code'] = df['cat02_code'].replace(replace_dict)

df = df[~df['国籍・地域'].str.contains('^うち')]

df.rename(columns={'value':'人口','unit':'単位','集計時点（半期毎）':'集計時点'}, inplace=True)
df=df.groupby(['tab_code', '表章項目', 'cat01_code', '在留資格', 'cat02_code', '国籍・地域','集計時点','単位']).sum().reset_index()

# print(df.head())

#######################################
# df3の準備
#######################################
# df側の表記を df3 に合わせる例
replace_dict ={
    'ジョージア（グルジア）':'ジョージア',
    'セントクリストファー・ネーヴィス':'セントクリストファー・ネービス',
    'エスワティニ':'スワジランド',
    '北米':'北アメリカ',
    '南米':'南アメリカ',
    'コソボ':'コソボ共和国',
    'スワジランド':'エスワティニ',
    'マケドニア':'北マケドニア',
    }
df3['国籍'] = df3['国籍'].replace(replace_dict)

df3['cat03_code']=df3['cat03_code']*10

df3 = df3.rename(columns={'在留資格（在留目的）':'在留資格','国籍':'国籍・地域','時間軸（年次）':'集計時点','unit':'単位','value':'人口','cat03_code':'cat02_code'})
df3['集計時点'] = df3['集計時点'].str.replace('年','年12月')

df3=df3.groupby(['tab_code', '表章項目', 'cat01_code', '在留資格', 'cat02_code', '国籍・地域','集計時点','単位']).sum().reset_index()

# print(df3.head())

################################
# dfとdf3を統合
################################
# 結合したいデータフレームを一つのリスト [ ] にまとめます
df_overall = pd.concat([
    df[(df['集計時点'].str.contains('12月|2025年6月'))],
    df3
], axis=0) # axis=0 は省略可能（縦方向の結合）

df_overall = df_overall[df_overall['人口']!='-']
df_overall['人口'] = df_overall['人口'].astype(float)

df_overall = df_overall.reset_index(drop=True)

print(df_overall.head())
df_overall.to_csv(DATA_DIR / 'zairyu_country.csv', index=False)

################################
# 在留外国人の推移
################################
