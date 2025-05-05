from flask import Flask, request, jsonify
import openai
import requests
import os
import base64
import fitz  # PyMuPDF
from io import BytesIO
import traceback
import json

app = Flask(__name__)

# 🔐 Environment Variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MATHPIX_APP_ID = os.environ.get("MATHPIX_APP_ID")
MATHPIX_APP_KEY = os.environ.get("MATHPIX_APP_KEY")
openai.api_key = OPENAI_API_KEY

# 🔍 PDF to Text via MathPix OCR
def extract_text_with_mathpix(pdf_file):
    extracted_text = ""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

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
            print(f"📄 OCR Page {i+1}:", page_text[:100])
            extracted_text += page_text + "\n"
        else:
            print(f"❌ MathPix OCR error (page {i+1}):", response.text)

    return extracted_text.strip()

# 🧠 GPT-Powered AI Tutor
@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        question = request.form.get("question", "").strip()
        history_raw = request.form.get("history", "[]")
        history = json.loads(history_raw)

        file = request.files.get("file")

        if not question:
            return jsonify({"error": "Missing question"}), 400

        # ✅ Step 1: System role prompt (always present)
        system_message = {
            "role": "system",
            "content": (
                "你是一位专门指导高考英语阅读理解的AI老师。"
                "请用中文回答学生的问题。"
                "如果学生提到某个题号（如Question 23），你需要结合之前的对话或上传的文章内容来回答。"
                "请不要要求重新上传或重复问题内容。你要作为一个有记忆的老师，直接回应。"
            )
        }

        messages = [system_message]

        # ✅ Step 2: File Upload (First Question)
        if file:
            print("📥 New PDF received.")
            extracted_text = extract_text_with_mathpix(file)

            if not extracted_text:
                return jsonify({"answer": "⚠️ OCR 无法识别任何文字，请上传清晰的 PDF 文件。"})

            content = f"以下是考生上传的PDF内容部分：\n{extracted_text}"
            messages.append({"role": "user", "content": content})

        else:
            # 🔁 Follow-Up with memory
            print("🔁 Follow-up question received.")
            for h in history:
                messages.append({
                    "role": "user" if "学生" in h["sender"] else "assistant",
                    "content": h["message"]
                })

        # ✅ Step 3: Append current student question
        messages.append({"role": "user", "content": question})

        print("🧠 GPT Message Flow:", messages[-3:])

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.3,
            max_tokens=600
        )

        answer = response["choices"][0]["message"]["content"].strip()
        if not answer:
            answer = "⚠️ AI 没有返回答案。请尝试更换问题或上传更清晰的 PDF。"

        print("✅ AI Answer:", answer[:200])
        return jsonify({"answer": answer})

    except Exception as e:
        print("❌ Backend error:", traceback.format_exc())
        return jsonify({"answer": f"⚠️ 服务器出错：{str(e)}"}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "✅ Gaokao AI Backend with 中文回答 + 记忆功能 is live."})
