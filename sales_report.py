import csv
from openpyxl import Workbook


def create_report(csv_path, output_path):
    total_quantity = 0
    total_sales = 0

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "売上レポート"

    sheet.append(["商品", "個数", "単価", "売上"])

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            product = row["商品"]
            quantity = int(row["個数"])
            price = int(row["単価"])
            sales = quantity * price

            total_quantity += quantity
            total_sales += sales

            sheet.append([product, quantity, price, sales])

    average_price = total_sales / total_quantity

    sheet.append([])
    sheet.append(["総個数", total_quantity])
    sheet.append(["総売上", total_sales])
    sheet.append(["平均単価", average_price])

    workbook.save(output_path)


csv_path = input("CSVファイルのパスを入力してください：")
output_path = "sales_report.xlsx"

create_report(csv_path, output_path)

print()
print("売上レポートを作成しました。")
print(f"保存先：{output_path}")