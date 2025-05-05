from flask import Flask, request, jsonify
import openai
import requests
import os
import base64
import fitz  # PyMuPDF
from io import BytesIO
import traceback

app = Flask(__name__)

# ✅ Environment Variables from Vercel
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MATHPIX_APP_ID = os.environ.get("MATHPIX_APP_ID")
MATHPIX_APP_KEY = os.environ.get("MATHPIX_APP_KEY")

openai.api_key = OPENAI_API_KEY

def extract_text_with_mathpix(pdf_file):
    extracted_text = ""

    # Open PDF with PyMuPDF
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

    # Read up to 3 pages
    for i, page in enumerate(doc.pages(0, min(3, doc.page_count))):
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        img_b64 = base64.b64encode(img_bytes).decode()

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
            page_text = result.get("text", "")
            print(f"📄 OCR Page {i+1}:", page_text[:200])
            extracted_text += page_text + "\n"
        else:
            print(f"❌ MathPix OCR error (page {i+1}):", response.text)

    return extracted_text.strip()

@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        if "file" not in request.files or "question" not in request.form:
            return jsonify({"error": "Missing file or question"}), 400

        file = request.files["file"]
        question = request.form["question"]

        # 🔍 Extract text from PDF
        extracted_text = extract_text_with_mathpix(file)

        if not extracted_text:
            return jsonify({"answer": "⚠️ OCR 无法识别任何文字，请上传清晰的 PDF 文件。"})

        # 📝 GPT prompt
        prompt = f"""
你是一位专门帮助高考学生理解阅读理解文章和考试题目的AI老师。

以下是从学生上传的PDF中提取的内容（部分节选）：

----------------
{extracted_text}
----------------

学生的问题如下：
{question}

请用中文详细地解释这个问题的答案，包括：
- 你如何理解这个问题
- 如何在文章中找到答案线索
- 对应的段落内容
- 推理过程
- 为什么这个答案是正确的

请确保语言清晰、逻辑完整，适合高中生理解。
"""

        print("📝 Prompt to OpenAI:", prompt[:500])

        ai_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )

        answer = ai_response["choices"][0]["message"]["content"].strip()
        if not answer:
            answer = "⚠️ AI 没有返回答案。请尝试更换问题或上传更清晰的 PDF。"

        print("✅ AI Answer:", answer[:300])
        return jsonify({"answer": answer})

    except Exception as e:
        print("❌ Backend error:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "✅ Gaokao AI Backend is live."})
