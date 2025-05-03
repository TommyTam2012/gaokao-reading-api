from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import openai
import os

app = FastAPI()

# ✅ Enable CORS for Replit → Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For security, replace with your actual Replit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load from Vercel Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MATHPIX_APP_ID = os.getenv("MATHPIX_APP_ID")
MATHPIX_APP_KEY = os.getenv("MATHPIX_APP_KEY")

openai.api_key = OPENAI_API_KEY

# MathPix OCR API
MATHPIX_URL = "https://api.mathpix.com/v3/pdf"

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        headers = {
            "app_id": MATHPIX_APP_ID,
            "app_key": MATHPIX_APP_KEY
        }
        files = {"file": (file.filename, await file.read(), file.content_type)}
        data = {"conversion_formats": {"markdown": True}}

        # Send to MathPix
        r = requests.post(MATHPIX_URL, headers=headers, files=files, data={"options_json": str(data)})
        r.raise_for_status()
        job = r.json()
        job_id = job.get("pdf_id")

        # Get markdown output
        text_result = requests.get(f"https://api.mathpix.com/v3/pdf/{job_id}.markdown",
                                   headers=headers)
        extracted_text = text_result.text

        return JSONResponse(content={"status": "success", "content": extracted_text})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/ask")
async def ask_question(question: str = Form(...), content: str = Form(...)):
    try:
        prompt = f"""
你是一位经验丰富的高考英语助教。以下是通过OCR系统识别并提取的试题内容，已经整理成纯文本格式：

【高考试卷内容】
{content}

现在有一位学生提问如下：
“{question}”

请你一步一步帮他解答，并按照下面的结构作答：

1. ✅ 正确答案（请只标出选项字母，如 A、B、C 或 D，并说明理由）
2. 📘 详细解释（使用简体中文解释为什么这个答案是正确的，包括关键句的定位、选项的差异、语法点或语义理解）
3. 🌱 学习建议（根据本题类型，给予学生提升的建议，比如词汇、长难句、干扰选项识别等）

请用简洁、清晰的中文回答，适合高中学生理解。
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        answer = response["choices"][0]["message"]["content"]
        return JSONResponse(content={"answer": answer})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
