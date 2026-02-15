import pandas as pd
from pathlib import Path

# スクリプトの場所を基準にパスを解決
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data' / 'jinkosuikei'

file1 = DATA_DIR / 'FEH_00200524_260204055744.csv'
file2 = DATA_DIR / 'FEH_00200524_260204055824.csv'
file3 = DATA_DIR / 'FEH_00200524_260204055907.csv'
file4 = DATA_DIR / 'FEH_00200524_260204101704.csv'
# 2025年月次
file5 = DATA_DIR / 'FEH_00200524_260204064018.csv'

df1 = pd.read_csv(file1,encoding='shift_jis')
df2 = pd.read_csv(file2,encoding='shift_jis')
df3 = pd.read_csv(file3,encoding='shift_jis')
df4 = pd.read_csv(file4,encoding='shift_jis')
df5 = pd.read_csv(file5,encoding='shift_jis')

df1 = df1[(df1['男女別']=='男女計')&(df1['全国・都道府県']=='全国')&(df1['時間軸（年）'].isin(['2020年','2021年','2022年','2023年','2024年']))].reset_index(drop=False)
df1 = df1[['時間軸（年）','人口','unit','value']]
df1 = df1.rename(columns = {'時間軸（年）':'時間軸'})
df2 = df2[(df2['男女別']=='男女計')&(df2['全国・都道府県']=='全国')&(df2['時間軸（年）'].isin(['2015年','2016年','2017年','2018年','2019年']))].reset_index(drop=False)
df2 = df2[['時間軸（年）','人口','unit','value']]
df2 = df2.rename(columns = {'時間軸（年）':'時間軸'})
df3 = df3[(df3['男女別']=='男女計')&(df3['全国・都道府県']=='全国')&(df3['時間軸（年）'].isin(['2010年','2011年','2012年','2013年','2014年']))].reset_index(drop=False)
df3 = df3[['時間軸（年）','人口','unit','value']]
df3 = df3.rename(columns = {'時間軸（年）':'時間軸'})
df4 = df4[(df4['男女別']=='男女計')&(df4['全国・都道府県']=='全国')&(df4['時間軸（年）'].isin(['2005年','2006年','2007年','2008年','2009年']))].reset_index(drop=False)
df4 = df4[['時間軸（年）','人口','unit','value']]
df4 = df4.rename(columns = {'時間軸（年）':'時間軸'})
df5 = df5[(df5['男女別']=='男女計')&(df5['年齢5歳階級']=='総数')&(df5['全国']=='全国')&(df5['時間軸（年月日現在）'].isin(['2025年6月']))].reset_index(drop=False)
df5 = df5[['時間軸（年月日現在）','人口','unit','value']]
df5 = df5.rename(columns = {'時間軸（年月日現在）':'時間軸'})

df = pd.concat([df1,df2,df3,df4,df5]).sort_values(['時間軸','人口'])
df = df.pivot_table(index='時間軸', columns='人口', values='value', aggfunc='first').reset_index()
df['外国人人口'] = df['総人口'] - df['日本人人口']
df['外国人比率'] = round(df['外国人人口'] / df['総人口'] * 100, 1)
OUTPUT_DIR = BASE_DIR / 'data'
df.to_csv(OUTPUT_DIR / 'jinkosuikei.csv', index=False)
print(df)