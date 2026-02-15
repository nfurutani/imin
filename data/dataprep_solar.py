import io
import requests
import pandas as pd
from pathlib import Path

BASE_URL = 'https://www.fit-portal.go.jp'

COLUMNS_NINTEI = [
    '設備ID', '発電事業者名', '代表者名', '事業者の住所', '事業者の電話番号',
    '発電設備区分', '発電出力kW', '代表住所', '他の筆数', '太陽電池の合計出力kW',
    '新規認定日', '運転開始予定日', '運転開始報告年月',
    '自立運転機能', '給電用コンセント', '廃棄費用の積立方法', '廃棄費用の積立状況', '調達期間終了年月',
]

COLUMNS_SHOZAICHI = [
    '設備ID', '発電事業者名', '連番', '代表者名', '発電設備区分',
    '発電出力kW', '発電設備の所在地', '太陽電池の合計出力kW',
]

PREF_LINKS = {
    '北海道': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuOS2AZ',
    '青森県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuOX2AZ',
    '岩手県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuOc2AJ',
    '宮城県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuOh2AJ',
    '秋田県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuOm2AJ',
    '山形県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuOr2AJ',
    '福島県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuOw2AJ',
    '茨城県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuP12AJ',
    '栃木県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuPB2AZ',
    '群馬県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuPG2AZ',
    '埼玉県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuPL2AZ',
    '千葉県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuLt2AJ',
    '東京都': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuPQ2AZ',
    '神奈川県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuPV2AZ',
    '新潟県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuPf2AJ',
    '富山県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuPk2AJ',
    '石川県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuNa2AJ',
    '福井県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuPp2AJ',
    '山梨県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuPu2AJ',
    '長野県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuPz2AJ',
    '岐阜県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuNp2AJ',
    '静岡県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuQ92AJ',
    '愛知県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuQJ2AZ',
    '三重県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuQO2AZ',
    '滋賀県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuQT2AZ',
    '京都府': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuQY2AZ',
    '大阪府': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuQd2AJ',
    '兵庫県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuQi2AJ',
    '奈良県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuQn2AJ',
    '和歌山県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuQs2AJ',
    '鳥取県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuQx2AJ',
    '島根県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuR22AJ',
    '岡山県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuR72AJ',
    '広島県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuRC2AZ',
    '山口県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuOY2AZ',
    '徳島県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuRH2AZ',
    '香川県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuRM2AZ',
    '愛媛県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuRR2AZ',
    '高知県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuRW2AZ',
    '福岡県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuRb2AJ',
    '佐賀県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuQP2AZ',
    '長崎県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuRg2AJ',
    '熊本県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuRl2AJ',
    '大分県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuRv2AJ',
    '宮崎県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuS02AJ',
    '鹿児島県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuS52AJ',
    '沖縄県': '/servlet/servlet.FileDownload?retURL=%2Fapex%2FPublicInfo&file=00PIT00002IcuSA2AZ',
}

DATA_DIR = Path(__file__).resolve().parent

frames_nintei = []
frames_shozaichi = []
for pref, path in PREF_LINKS.items():
    print(f'{pref}... ', end='', flush=True)
    r = requests.get(BASE_URL + path)
    r.raise_for_status()
    content = io.BytesIO(r.content)

    # 認定設備シート
    df1 = pd.read_excel(content, sheet_name='認定設備', header=None, skiprows=4)
    df1 = df1.iloc[:, 1:]
    df1.columns = COLUMNS_NINTEI
    df1['都道府県'] = pref
    frames_nintei.append(df1)

    # すべての設備所在地シート
    content.seek(0)
    df2 = pd.read_excel(content, sheet_name='すべての設備所在地', header=None, skiprows=2)
    df2 = df2.iloc[:, 1:]
    df2.columns = COLUMNS_SHOZAICHI
    df2['都道府県'] = pref
    frames_shozaichi.append(df2)

    print(f'認定{len(df1):,}件 / 所在地{len(df2):,}件')


def save_parquet(frames, name):
    df = pd.concat(frames, ignore_index=True)
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).replace('nan', '')
    out = DATA_DIR / f'{name}.parquet'
    df.to_parquet(out, index=False)
    print(f'{name}: {len(df):,}件 → {out}')


save_parquet(frames_nintei, 'solar_nintei')
save_parquet(frames_shozaichi, 'solar_shozaichi')
