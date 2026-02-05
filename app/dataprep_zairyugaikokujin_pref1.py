import pandas as pd
from pathlib import Path

# スクリプトの場所を基準にパスを解決
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'/ 'zairyu'

def set_column_names(df):
  # 0行目を列名にする
  df.columns = df.iloc[0]
  # 0行目を削除してリセット
  df = df.drop(0).reset_index(drop=True)
  return df

df_isa = pd.DataFrame()
item = {"year":2025, "url":"https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040379765&fileKind=0","filename":"25-06-t1.xlsx"}
year = item['year']
column_name = '人口_'+str(year)
url = item['url']
filename = DATA_DIR / item['filename']

df = pd.read_excel(filename, header=None, skiprows=7)
df = set_column_names(df)


# 重複カラムを確認
print("カラム数:", len(df.columns))
print("ユニークなカラム数:", len(df.columns.unique()))

df = df.rename(columns={df.columns[0]: '都道府県'})

# 不要な行とカラムを削除
df = df[df['都道府県']!='総計']
if '総計' in df.columns:
    df = df.drop(columns=['総計'])

df = df.set_index('都道府県')

# stack()してSeriesを作成
stacked = df.stack()

# インデックス名を確認
print("\nインデックスレベル名:", stacked.index.names)

# to_frame()でDataFrameに変換してreset_index()
df = stacked.to_frame('population').reset_index()

# level_1（元のカラム名）を'country'にリネーム
if 'level_1' in df.columns:
    df = df.rename(columns={'level_1': '国名'})
elif len(df.columns) == 3:
    df.columns = ['都道府県', '国籍', column_name]

# continentカラムを追加：countryの_の前の数字を抽出
df['地域番号'] = df['国籍'].str.extract(r'^(\d+)_', expand=False)

# 大陸コードの対応表
continent_map = {
    '01': 'アジア',
    '02': 'ヨーロッパ',
    '03': 'アフリカ',
    '04': '北米',
    '05': '南米',
    '06': 'オセアニア',
    '07': '無国籍',
    '08': '無国籍'
}

# 大陸コードを名前に変換
df['地域'] = df['地域番号'].map(continent_map)

# 国名から「01_001：アフガニスタン」→「アフガニスタン」を抽出
df['国籍'] = df['国籍'].str.split('：').str[1]


# continentカラムを追加：countryの_の前の数字を抽出
df['都道府県番号'] = df['都道府県'].str.extract(r'^(\d+)：', expand=False)

# 国名から「01：北海道」→「北海道」を抽出
df['都道府県'] = df['都道府県'].str.split('：').str[1]

# 数値であることを確認
df[column_name] = df[column_name].astype(float)


print("\n最終データ:")
print(df.tail(20))
print(f"\nShape: {df.shape}")

# 大陸別の集計を確認
print("\n大陸別のカウント:")
print(df['地域'].value_counts())

# CSVに保存
OUTPUT_DIR = BASE_DIR / 'data'
df.to_csv(OUTPUT_DIR / 'zairyu_pref.csv', index=False)
print(f"\n保存完了: {OUTPUT_DIR / 'zairyu_pref.csv'}")