from flask import Flask, request, jsonify
import openai
import requests
import os

app = Flask(__name__)

# ✅ Environment variables (set in Vercel)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MATHPIX_APP_ID = os.environ.get("MATHPIX_APP_ID")
MATHPIX_APP_KEY = os.environ.get("MATHPIX_APP_KEY")

openai.api_key = OPENAI_API_KEY

@app.route("/api/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files or "question" not in request.form:
        return jsonify({"error": "Missing file or question"}), 400

    file = request.files["file"]
    question = request.form["question"]
    history_raw = request.form.get("history", "[]")

    # 📄 Send file to MathPix for OCR
    files = {"file": file}
    headers = {"app_id": MATHPIX_APP_ID, "app_key": MATHPIX_APP_KEY}
    mathpix_url = "https://api.mathpix.com/v3/text"

    mathpix_response = requests.post(mathpix_url, files=files, headers=headers)
    if mathpix_response.status_code != 200:
        return jsonify({"error": "MathPix OCR failed"}), 500

    result = mathpix_response.json()
    document_text = result.get("text", "")

    if not document_text:
        return jsonify({"answer": "⚠️ OCR 无法识别任何文字，请上传清晰的 PDF 文件。"})

    # 🤖 Ask OpenAI based on document + question
    prompt = f"""以下是考生上传的试题内容片段：

{document_text}

问题如下：{question}

请根据文档内容提供简洁准确的回答："""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        answer = response["choices"][0]["message"]["content"].strip()
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "✅ Gaokao Reading API is live on Vercel."})
