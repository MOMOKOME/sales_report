# CSV売上レポート

CSVの売上データを集計し、結果をWeb画面で確認してExcelレポートをダウンロードできるFlaskアプリです。コマンドラインからExcelを作ることもできます。

## できること

- 商品別明細、総個数、総売上、平均単価を表示
- 「日付」「カテゴリ」列がある場合、それぞれの売上も集計
- 集計結果を複数シートのExcelブックとして出力
- CSVの列不足や不正な数値を日本語で案内

## 使用技術

Python 3.9以上、Flask、openpyxl、HTML、CSS、Python標準CSVモジュール

## インストール

PowerShellでプロジェクトのフォルダーに移動し、次を実行します。

`powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
`

macOS / Linuxでは source .venv/bin/activate で仮想環境を有効にします。

## 起動方法

Webアプリを起動します。

`powershell
python app.py
`

ブラウザーで <http://127.0.0.1:5000> を開きます。CLIでExcelを作る場合は次を実行します。

`powershell
python sales_report.py sales.csv --output sales_report.xlsx
`

## CSVの必要な列

必須列は 商品, 個数, 単価 です。個数と単価は0以上の整数を指定してください。文字コードはUTF-8（BOM付きも可）です。日付 と カテゴリ は任意列で、指定すると追加集計します。

`csv
商品,個数,単価,日付,カテゴリ
りんご,3,100,2026-09-01,果物
バナナ,2,150,2026-09-01,果物
`

## Web版の使い方

1. トップページでCSVファイルを選びます。
2. アップロードして集計結果を確認します。
3. 「Excelレポートをダウンロード」からブックを保存します。

アップロード上限は2MBです。CSVは一時フォルダーで処理し、アップロードしたファイル自体はプロジェクトに保存しません。集計結果はダウンロード用に一時的にメモリーへ保持します。

## Excelダウンロード

明細と全体集計を含む「売上レポート」シートを作成します。CSVに「日付」または「カテゴリ」列がある場合は、それぞれの集計シートも追加します。

## テスト

`powershell
python -m unittest discover -s tests -v
`
