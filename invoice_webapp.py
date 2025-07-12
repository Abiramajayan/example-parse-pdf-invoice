from flask import Flask, request, jsonify, send_file
import io
import csv
from pdf2image import convert_from_bytes
import pytesseract

app = Flask(__name__)


def ocr_pdf(file_bytes: bytes) -> str:
    """Run OCR on each page of the PDF and return concatenated text."""
    images = convert_from_bytes(file_bytes)
    pages = []
    for img in images:
        pages.append(pytesseract.image_to_string(img))
    return "\n".join(pages)


def extract_invoice_data(text: str) -> dict:
    """Very basic extraction of a few invoice fields."""
    data = {}
    import re
    date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", text)
    if date_match:
        data["date"] = date_match.group(1)
    total_match = re.search(r"Total[^\d]*(\d+[\.,]\d{2})", text, re.IGNORECASE)
    if total_match:
        data["total"] = total_match.group(1)
    return data


@app.route("/", methods=["GET"])
def index():
    return (
        "<h1>Invoice OCR</h1>"
        "<form method='post' action='/upload' enctype='multipart/form-data'>"
        "<input type='file' name='file'/><input type='submit'/></form>"
    )


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    text = ocr_pdf(file.read())
    data = extract_invoice_data(text)

    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data.keys())
        writer.writeheader()
        writer.writerow(data)
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype="text/csv",
            as_attachment=True,
            download_name="invoice.csv",
        )
    return jsonify({"text": text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
