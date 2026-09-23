"""CSV validation and sales aggregation shared by the CLI and web app."""

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

PRODUCT = "\u5546\u54c1"
QUANTITY = "\u500b\u6570"
PRICE = "\u5358\u4fa1"
SALES = "\u58f2\u4e0a"
DATE = "\u65e5\u4ed8"
CATEGORY = "\u30ab\u30c6\u30b4\u30ea"


class SalesReportError(Exception):
    """An expected, user-correctable sales report error."""


@dataclass
class SalesReport:
    rows: list
    total_quantity: int
    total_sales: int
    average_price: float
    product_totals: dict
    date_totals: dict
    category_totals: dict


def load_and_aggregate(csv_path):
    """Read a UTF-8 CSV, validate required columns, and calculate totals."""
    path = Path(csv_path)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source, strict=True)
            headers = reader.fieldnames
            if not headers or not any((header or "").strip() for header in headers):
                return SalesReport([], 0, 0, 0.0, {}, {}, {})
            required = (PRODUCT, QUANTITY, PRICE)
            missing = [name for name in required if name not in headers]
            if missing:
                raise SalesReportError("\u5fc5\u8981\u306a\u5217\u304c\u3042\u308a\u307e\u305b\u3093: " + ", ".join(missing))
            rows = []
            for row in reader:
                line_number = reader.line_num
                if None in row:
                    raise SalesReportError(f"{line_number}\u884c\u76ee: \u5217\u6570\u304c\u30d8\u30c3\u30c0\u30fc\u3068\u4e00\u81f4\u3057\u307e\u305b\u3093\u3002")
                product = (row.get(PRODUCT) or "").strip()
                if not product:
                    raise SalesReportError(f"{line_number}\u884c\u76ee: \u5546\u54c1\u540d\u304c\u7a7a\u3067\u3059\u3002")
                try:
                    quantity = int((row.get(QUANTITY) or "").strip())
                    price = int((row.get(PRICE) or "").strip())
                except ValueError as error:
                    raise SalesReportError(f"{line_number}\u884c\u76ee: \u500b\u6570\u3068\u5358\u4fa1\u306f\u6574\u6570\u3067\u5165\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002") from error
                if quantity < 0 or price < 0:
                    raise SalesReportError(f"{line_number}\u884c\u76ee: \u500b\u6570\u3068\u5358\u4fa1\u306b\u8ca0\u306e\u5024\u306f\u4f7f\u3048\u307e\u305b\u3093\u3002")
                item = {"product": product, "quantity": quantity, "price": price, "sales": quantity * price}
                for optional in (DATE, CATEGORY):
                    if optional in headers:
                        item["date" if optional == DATE else "category"] = (row.get(optional) or "").strip()
                rows.append(item)
    except SalesReportError:
        raise
    except FileNotFoundError as error:
        raise SalesReportError(f"CSV\u30d5\u30a1\u30a4\u30eb\u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093: {path}") from error
    except (OSError, UnicodeError, csv.Error) as error:
        raise SalesReportError(f"CSV\u3092\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093: {error}") from error
    if not rows:
        return SalesReport([], 0, 0, 0.0, {}, {}, {})
    total_quantity = sum(row["quantity"] for row in rows)
    total_sales = sum(row["sales"] for row in rows)

    def aggregate(key):
        totals = defaultdict(lambda: {"quantity": 0, "sales": 0})
        for row in rows:
            label = row.get(key)
            if label:
                totals[label]["quantity"] += row["quantity"]
                totals[label]["sales"] += row["sales"]
        return dict(totals)

    return SalesReport(rows, total_quantity, total_sales,
                       total_sales / total_quantity if total_quantity else 0.0,
                       aggregate("product"), aggregate("date"), aggregate("category"))
