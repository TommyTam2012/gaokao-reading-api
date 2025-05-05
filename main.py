from flask import Flask, request, jsonify
import openai
import requests
import os
import base64
from pdf2image import convert_from_bytes
from io import BytesIO

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MATHPIX_APP_ID = os.environ.get("MATHPIX_APP_ID")
MATHPIX_APP_KEY = os.environ.get("MATHPIX_APP_KEY")

openai.api_key = OPENAI_API_KEY

def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def extract_text_with_mathpix(pdf_file):
    pages = convert_from_bytes(pdf_file.read(), dpi=200)
    extracted_text = ""

    for i, page in enumerate(pages[:3]):
        img_b64 = image_to_base64(page)
        headers = {
            "app_id": MATHPIX_APP_ID,
            "app_key": MATHPIX_APP_KEY,
            "Content-type": "application/json"
        }
        data = {
            "src": f"data:image/png;base64,{img_b64}",
            "formats": ["text"],
            "ocr": ["math", "text"]
        }

        response = requests.post("https://api.mathpix.com/v3/text", json=data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            extracted_text += result.get("text", "") + "\n"
        else:
            print(f"MathPix OCR error (page {i+1}):", response.text)

    return extracted_text.strip()

@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        if "file" not in request.files or "question" not in request.form:
            return jsonify({"error": "Missing file or question"}), 400

        file = request.files["file"]
        question = request.form["question"]

        # 🧠 Extract text from scanned PDF
        extracted_text = extract_text_with_mathpix(file)

        if not extracted_text:
            return jsonify({"answer": "⚠️ OCR 无法识别任何文字，请上传清晰的 PDF 文件。"})

        prompt = f"""以下是文档内容：

{extracted_text}

问题如下：{question}

请基于文档内容回答："""

        ai_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )

        answer = ai_response["choices"][0]["message"]["content"].strip()
        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "✅ Gaokao AI Backend is live."})
