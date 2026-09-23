import io
import unittest

from app import create_app, _reports


class SalesReportWebTests(unittest.TestCase):
    def setUp(self):
        _reports.clear()
        self.app = create_app({"TESTING": True})
        self.client = self.app.test_client()

    def upload(self, contents, filename="sales.csv"):
        return self.client.post("/report", data={"file": (io.BytesIO(contents), filename)},
                                content_type="multipart/form-data", follow_redirects=True)

    def test_homepage_opens_with_japanese_utf8_content(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"&#x58f2;&#x4e0a;", response.data)
        self.assertNotIn("\ufffd".encode("utf-8"), response.data)

    def test_csv_upload_shows_totals_and_japanese_item(self):
        data = "\u5546\u54c1,\u500b\u6570,\u5358\u4fa1\n\u308a\u3093\u3054,3,100\n\u30d0\u30ca\u30ca,2,150\n".encode("utf-8")
        response = self.upload(data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("\u308a\u3093\u3054".encode("utf-8"), response.data)
        self.assertIn(b"&yen;600", response.data)
        self.assertNotIn("\ufffd".encode("utf-8"), response.data)

    def test_invalid_csv_shows_japanese_error(self):
        response = self.upload("\u5546\u54c1,\u500b\u6570\na,1\n".encode("utf-8"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("\u5fc5\u8981\u306a\u5217\u304c\u3042\u308a\u307e\u305b\u3093".encode("utf-8"), response.data)

    def test_empty_csv_displays_empty_state(self):
        response = self.upload(b"")
        self.assertEqual(response.status_code, 200)
        self.assertIn("&#x660e;&#x7d30;&#x884c;".encode(), response.data)

    def test_missing_file_shows_japanese_error(self):
        response = self.client.post("/report", data={}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("\u30d5\u30a1\u30a4\u30eb\u3092\u9078\u629e".encode("utf-8"), response.data)

    def test_non_csv_is_rejected(self):
        response = self.upload(b"not csv", "sales.xlsx")
        self.assertIn("CSV\u30d5\u30a1\u30a4\u30eb".encode("utf-8"), response.data)

    def test_excel_download_has_japanese_workbook_content(self):
        data = "\u5546\u54c1,\u500b\u6570,\u5358\u4fa1\n\u308a\u3093\u3054,1,100\n".encode("utf-8")
        response = self.upload(data)
        self.assertEqual(response.status_code, 200)
        report_id = next(iter(_reports))
        download = self.client.get(f"/download/{report_id}")
        self.assertEqual(download.status_code, 200)
        self.assertTrue(download.data.startswith(b"PK"))

    def test_oversized_upload_is_rejected(self):
        self.app.config["MAX_CONTENT_LENGTH"] = 32
        response = self.upload(b"x" * 100)
        self.assertEqual(response.status_code, 413)


if __name__ == "__main__":
    unittest.main()
