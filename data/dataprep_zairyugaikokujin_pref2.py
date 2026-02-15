import pandas as pd
from pathlib import Path


# スクリプトの場所を基準にパスを解決
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data' / 'zairyu'

###############################################
# 202506のデータ
################################################
file_202506 = DATA_DIR / '001447922.xlsx'
df_202506_country = pd.read_excel(file_202506, sheet_name='第５表 ', skiprows=1)
df_202506_country = df_202506_country.drop(df_202506_country.columns[0], axis=1)

df_202506_status = pd.read_excel(file_202506, sheet_name='第６表', skiprows=2)
df_202506_status = df_202506_status.drop(df_202506_status.columns[0], axis=1)
df_202506_status.columns = ['都道府県','総数','中長期在留者','永住者','技術・人文知識・国際業務','技能実習','留学','特定技能','家族滞在','定住者','日本人の配偶者等','特定活動','その他','特別永住者']
df_202506_status = df_202506_status.drop(columns='中長期在留者')

print(df_202506_country.columns)
print(df_202506_status.columns)

###############################################
# 202406のデータ
################################################
file_202406 = DATA_DIR / '001425982.xlsx'
df_202406_country = pd.read_excel(file_202406, sheet_name='第５表', skiprows=1)
df_202406_country = df_202406_country.drop(df_202406_country.columns[0], axis=1)

df_202406_status = pd.read_excel(file_202406, sheet_name='第６表', skiprows=2)
df_202406_status = df_202406_status.drop(df_202406_status.columns[0], axis=1)
df_202406_status.columns = ['都道府県','総数','中長期在留者','永住者','技能実習','技術・人文知識・国際業務','留学','家族滞在','特定技能','定住者','日本人の配偶者等','特定活動','その他','特別永住者']
df_202406_status = df_202406_status.drop(columns='中長期在留者')

# print(df_202406_country.head())
# print(df_202406_status.head())

###############################################
# melt処理（縦持ち変換）
###############################################
def melt_country(df, year):
    """国籍別データをmelt"""
    first_col = df.columns[0]
    df_melted = df.melt(id_vars=[first_col], var_name='国籍', value_name=f'{year}/06')
    df_melted = df_melted.rename(columns={first_col: '都道府県'})
    return df_melted

def melt_status(df, year):
    """在留資格別データをmelt"""
    first_col = df.columns[0]
    df_melted = df.melt(id_vars=[first_col], var_name='在留資格', value_name=f'{year}/06')
    df_melted = df_melted.rename(columns={first_col: '都道府県'})
    return df_melted

# 国籍別
df_202406_country_melted = melt_country(df_202406_country, 2024)
df_202506_country_melted = melt_country(df_202506_country, 2025)

# 在留資格別
df_202406_status_melted = melt_status(df_202406_status, 2024)
df_202506_status_melted = melt_status(df_202506_status, 2025)

# print("=== 国籍別 2024 ===")
# print(df_202406_country_melted.head())
# print("\n=== 国籍別 2025 ===")
# print(df_202506_country_melted.head())
# print("\n=== 在留資格別 2024 ===")
# print(df_202406_status_melted.head())
# print("\n=== 在留資格別 2025 ===")
# print(df_202506_status_melted.head())

df_country = pd.merge(df_202406_country_melted, df_202506_country_melted, on=['都道府県','国籍'], how='left')
# df_country = df_country[df_country['国籍']!='総数']

df_status = pd.merge(df_202406_status_melted, df_202506_status_melted, on=['都道府県','在留資格'], how='left')
# df_status = df_status[df_status['在留資格']!='総数']

# 縦持ちに変換（グラフ用）
df_country_long = df_country.melt(
    id_vars=['都道府県', '国籍'],
    value_vars=['2024/06', '2025/06'],
    var_name='時点',
    value_name='人口'
)

df_status_long = df_status.melt(
    id_vars=['都道府県', '在留資格'],
    value_vars=['2024/06', '2025/06'],
    var_name='時点',
    value_name='人口'
)

###############################################
# 韓国・朝鮮を統一
###############################################
df_country_long['国籍'] = df_country_long['国籍'].replace({'韓国': '韓国・朝鮮', '朝鮮': '韓国・朝鮮'})
df_country_long = df_country_long.groupby(['都道府県', '国籍', '時点'], as_index=False)['人口'].sum()

print("\n=== 国籍別 ===")
print(df_country_long.head())
print("\n=== 在留資格別 ===")
print(df_status_long.head())

# CSV出力
OUTPUT_DIR = BASE_DIR / 'data'
df_country_long.to_csv(OUTPUT_DIR / 'zairyu_pref_country.csv', index=False)
df_status_long.to_csv(OUTPUT_DIR / 'zairyu_pref_status.csv', index=False)
print(f"\n保存完了: {OUTPUT_DIR / 'zairyu_pref_country.csv'}")
print(f"保存完了: {OUTPUT_DIR / 'zairyu_pref_status.csv'}")

print(df_status_long[df_status_long['都道府県']=='長野県'])