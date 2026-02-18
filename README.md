# OpenJP

太陽光発電（メガソーラー）と在留外国人に関する政府統計をビジュアライズするWebアプリです。
URL: https://audio-demo-aessqzj9nw3cdrfsjvjmn8.streamlit.app/

## セットアップ

```bash
git clone https://github.com/chkdai/imin.git
cd imin
python3 -m venv .venv
source .venv/bin/activate       # Linux / macOS
pip install -r requirements.txt
streamlit run app/app.py
deactivate                      # 終了時
```

## データ整備

データは `data/dataprep_*.py` スクリプトを手動実行して生成します。

### `dataprep_solar.py` — FIT認定設備データ

```bash
python data/dataprep_solar.py
```

| 項目 | 内容 |
|---|---|
| 提供元 | 経済産業省 [再生可能エネルギー発電事業計画 認定情報](https://www.fit-portal.go.jp/) |
| 内容 | 全国の太陽光発電設備（FIT認定）の出力・所在地・運転状況 |
| 更新頻度 | 毎月 |
| 出力ファイル | `data/solar_nintei.parquet` |

---

### `dataprep_geo.py` — 行政区域GeoJSON

```bash
python data/dataprep_geo.py
```

| 項目 | 内容 |
|---|---|
| 提供元 | 国土交通省 国土数値情報 行政区域データ（[smartnews-smri/japan-topography](https://github.com/smartnews-smri/japan-topography) 経由） |
| 内容 | 都道府県・市区町村の境界ポリゴン |
| 基準日 | 2021年1月1日（行政区域変更がない限り更新不要） |
| 出力ファイル | `data/geo/prefectures.geojson`, `data/geo/{都道府県}.geojson` |

---

### `dataprep_daicho_estat.py` — 住民基本台帳人口

```bash
python data/dataprep_daicho_estat.py
```

| 項目 | 内容 |
|---|---|
| 提供元 | 総務省 [住民基本台帳に基づく人口、人口動態及び世帯数](https://www.soumu.go.jp/main_sosiki/jichi_gyousei/daityo/jinkou_jinkoudoutai-setaisuu.html) / [e-Stat](https://www.e-stat.go.jp/) |
| 内容 | 都道府県・市区町村別の総人口・外国人人口（2013〜2025年） |
| 基準日 | 毎年1月1日 |
| 次回更新 | 2026年1月1日基準データ（公表は2026年夏頃の見込み） |
| 出力ファイル | `data/daicho_estat.csv` |

---

### `dataprep_zairyugaikokujin.py` — 在留外国人統計（国籍別推移）

```bash
python data/dataprep_zairyugaikokujin.py
```

| 項目 | 内容 |
|---|---|
| 提供元 | 出入国在留管理庁 [在留外国人統計](https://www.moj.go.jp/isa/policies/statistics/toukei_ichiran_touroku.html) |
| 内容 | 国籍・在留資格別の在留外国人数推移（2012年12月〜2025年6月） |
| 更新頻度 | 半年ごと（6月末・12月末基準） |
| 次回更新 | 2025年12月末基準データ（公表は2026年3月頃の見込み） |
| 入力ファイル | `data/zairyu/*.csv`（e-Stat からダウンロードして配置） |
| 出力ファイル | `data/zairyu_country.csv` |

---

### `dataprep_zairyugaikokujin_pref2.py` — 在留外国人統計（都道府県別）

```bash
python data/dataprep_zairyugaikokujin_pref2.py
```

| 項目 | 内容 |
|---|---|
| 提供元 | 出入国在留管理庁 [在留外国人統計](https://www.moj.go.jp/isa/policies/statistics/toukei_ichiran_touroku.html) |
| 内容 | 都道府県・国籍別、都道府県・在留資格別の在留外国人数（2024年6月・2025年6月） |
| 更新頻度 | 半年ごと（6月末・12月末基準） |
| 次回更新 | 2025年12月末基準データ（公表は2026年3月頃の見込み） |
| 入力ファイル | `data/zairyu/*.xlsx`（法務省からダウンロードして配置） |
| 出力ファイル | `data/zairyu_pref_country.csv`, `data/zairyu_pref_status.csv` |
