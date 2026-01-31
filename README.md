# jp_visualization
時事ネタをe-statとstreamlitで可視化

## 仮想環境構築(venv)
```
# 仮想環境作成
python3 -m venv .venv

# 有効化 (Linux / macOS)
source .venv/bin/activate

# 必要なライブラリをインストール
pip install streamlit
pip freeze > requirements.txt

# 使い終わったら仮想環境を無効化
deactivate
```
## 使用データ

[総務省 住民基本台帳に基づく人口、人口動態及び世帯数](https://www.soumu.go.jp/main_sosiki/jichi_gyousei/daityo/jinkou_jinkoudoutai-setaisuu.html)
- 【総計】令和7年住民基本台帳人口・世帯数、令和6年人口動態（市区町村別）EXCEL
- 【外国人住民】令和7年住民基本台帳人口・世帯数、令和6年人口動態（市区町村別）EXCEL