"""Flask web interface for uploading and viewing sales reports."""

from collections import OrderedDict
from io import BytesIO
from pathlib import Path
import secrets
import tempfile
import time
import uuid

from flask import Flask, abort, flash, redirect, render_template, request, send_file, url_for

from sales_report import write_excel
from sales_report_core import SalesReportError, load_and_aggregate

MAX_REPORTS = 8
REPORT_TTL_SECONDS = 30 * 60
_reports = OrderedDict()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(SECRET_KEY=secrets.token_bytes(32), MAX_CONTENT_LENGTH=2 * 1024 * 1024)
    if test_config:
        app.config.update(test_config)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/report")
    def report():
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            flash("\u30d5\u30a1\u30a4\u30eb\u3092\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044\u3002", "error")
            return redirect(url_for("index"))
        if Path(upload.filename).suffix.lower() != ".csv":
            flash("CSV\u30d5\u30a1\u30a4\u30eb\u3092\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044\u3002", "error")
            return redirect(url_for("index"))
        try:
            with tempfile.TemporaryDirectory(prefix="sales-report-") as directory:
                csv_path = Path(directory) / "upload.csv"
                upload.save(csv_path)
                result = load_and_aggregate(csv_path)
        except SalesReportError as error:
            flash(str(error), "error")
            return redirect(url_for("index"))
        except OSError:
            app.logger.exception("Could not process uploaded report")
            flash("CSV\u3092\u51e6\u7406\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f\u3002", "error")
            return redirect(url_for("index"))
        _expire_reports()
        report_id = uuid.uuid4().hex
        _reports[report_id] = (time.monotonic(), result)
        while len(_reports) > MAX_REPORTS:
            _reports.popitem(last=False)
        return render_template("report.html", report=result, report_id=report_id)

    @app.get("/download/<report_id>")
    def download(report_id):
        _expire_reports()
        cached = _reports.get(report_id)
        if cached is None:
            abort(404)
        stream = BytesIO()
        try:
            write_excel(cached[1], stream)
        except SalesReportError:
            app.logger.exception("Could not create Excel report")
            flash("Excel\u30ec\u30dd\u30fc\u30c8\u3092\u4f5c\u6210\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f\u3002", "error")
            return redirect(url_for("index"))
        stream.seek(0)
        return send_file(stream, as_attachment=True, download_name="sales_report.xlsx",
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    @app.errorhandler(413)
    def too_large(_error):
        flash("CSV\u30d5\u30a1\u30a4\u30eb\u306f2MB\u4ee5\u4e0b\u306b\u3057\u3066\u304f\u3060\u3055\u3044\u3002", "error")
        return render_template("index.html"), 413

    return app


def _expire_reports():
    cutoff = time.monotonic() - REPORT_TTL_SECONDS
    for report_id, (created_at, _report) in list(_reports.items()):
        if created_at < cutoff:
            _reports.pop(report_id, None)


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
