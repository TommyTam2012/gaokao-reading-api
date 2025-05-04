from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import openai
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ← allow all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MATHPIX_APP_ID = os.getenv("MATHPIX_APP_ID")
MATHPIX_APP_KEY = os.getenv("MATHPIX_APP_KEY")

openai.api_key = OPENAI_API_KEY
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

        r = requests.post(MATHPIX_URL, headers=headers, files=files, data={"options_json": str(data)})
        r.raise_for_status()
        job = r.json()
        job_id = job.get("pdf_id")

        text_result = requests.get(f"https://api.mathpix.com/v3/pdf/{job_id}.markdown", headers=headers)
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

        return JSONResponse(content={"answer": response["choices"][0]["message"]["content"]})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.options("/{any_path:path}")
async def preflight(any_path: str):
    return JSONResponse(content={"message": "CORS OK"})
@app.get("/")
async def home():
    return JSONResponse(content={"message": "✅ Gaokao Reading API is live on Vercel."})
@app.post("/followup")
async def ask_followup_question(
    followup_question: str = Form(...),
    content: str = Form(...),
    question: str = Form(...),
    previous_answer: str = Form(...)
):
    try:
        prompt = f"""
你是一位经验丰富的高考英语助教。以下是学生通过OCR上传的阅读材料：

【高考试卷内容】
{content}

学生之前提出的问题：
“{question}”

你给出的原始答案是：
{previous_answer}

现在学生又提出了一个新的问题：
“{followup_question}”

请你参考原始内容、原始提问和你之前的回答，来回答学生的新问题。

请用下面的格式作答：

1. ✅ 逻辑回应（围绕学生当前的问题展开）
2. 📘 中文解释（引用原文片段，解释你的推理）
3. 🌱 学习建议（帮助学生理解类似题型）

请用简洁清晰的中文回答，适合高中生理解。
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        return JSONResponse(content={"answer": response["choices"][0]["message"]["content"]})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
