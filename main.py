from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json
import traceback
from ocr import extract_text_with_mathpix

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/")
def index():
    return "✅ AI Gaokao Reading System is running."

@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        question = request.form.get("question", "").strip()
        history_raw = request.form.get("history", "[]")
        history = json.loads(history_raw)
        file = request.files.get("file")

        if not question:
            return jsonify({"error": "Missing question"}), 400

        # 🧠 Step 1: Persistent system prompt
        messages = [{
            "role": "system",
            "content": (
                "你是一位专门指导高考英语阅读理解的AI老师。"
                "请用中文解答学生的问题，逻辑清晰，语言通俗易懂，引用原文支持你的观点。"
                "如果学生提到某个题号（例如 Question 22），请在上下文中查找相关内容，"
                "并详细解释为什么选择该答案。"
            )
        }]

        # 📄 Step 2: Handle new upload
        if file:
            print("📥 New PDF received.")
            extracted_text = extract_text_with_mathpix(file)

            if not extracted_text:
                return jsonify({"answer": "⚠️ OCR 无法识别任何文字，请上传清晰的 PDF 文件。"})

            content_message = f"以下是考生上传的PDF内容摘录：\n{extracted_text}"
            messages.append({"role": "user", "content": content_message})

        else:
            print("🔁 Follow-up question received.")
            for h in history:
                messages.append({
                    "role": "user" if "学生" in h["sender"] else "assistant",
                    "content": h["message"]
                })

        # ➕ Step 3: Add current question
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
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
