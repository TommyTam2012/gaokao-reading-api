pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.14.305/pdf.worker.min.js';

let pdfDoc = null;
let currentPage = 1;
let totalPages = 0;
let uploadedPDF = null;
let conversationHistory = [];

// ⛵ File Upload Handler
function handleFileUpload() {
  const fileInput = document.getElementById("pdfFile");
  const file = fileInput.files[0];

  console.log("🟢 File selected:", file?.name);

  if (!file || file.type !== "application/pdf") {
    alert("请选择一个有效的 PDF 文件");
    return;
  }

  uploadedPDF = file;

  const reader = new FileReader();
  reader.onload = function () {
    const typedArray = new Uint8Array(this.result);

    pdfjsLib.getDocument(typedArray).promise.then(function (pdf) {
      pdfDoc = pdf;
      totalPages = pdf.numPages;
      currentPage = 1;

      document.getElementById("pageCount").textContent = totalPages;
      renderPage(currentPage);
    });
  };
  reader.readAsArrayBuffer(file);
}

// ⬅️ ➡️ PDF Page Navigation
function renderPage(pageNum) {
  pdfDoc.getPage(pageNum).then(function (page) {
    const viewport = page.getViewport({ scale: 1.3 });
    const canvas = document.getElementById("pdfCanvas");
    const context = canvas.getContext("2d");

    canvas.height = viewport.height;
    canvas.width = viewport.width;

    const renderContext = {
      canvasContext: context,
      viewport: viewport
    };

    page.render(renderContext);
    document.getElementById("pageNumber").textContent = pageNum;
  });
}

function prevPage() {
  if (currentPage <= 1) return;
  currentPage--;
  renderPage(currentPage);
}

function nextPage() {
  if (currentPage >= totalPages) return;
  currentPage++;
  renderPage(currentPage);
}

// 🚀 Submit Question to AI
async function submitQuestion() {
  const question = document.getElementById('questionInput').value.trim();
  if (!uploadedPDF) {
    alert("请先上传PDF文件");
    return;
  }
  if (!question) {
    alert("请输入问题");
    return;
  }

  addToHistory("🧑‍🎓 学生", question);

  const formData = new FormData();
  formData.append("file", uploadedPDF);
  formData.append("question", question);
  formData.append("history", JSON.stringify(conversationHistory));

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData
    });

    const result = await response.json();
    const aiReply = result.answer || result.message || "AI 没有返回答案";

    document.getElementById("responseBox").textContent = aiReply;
    addToHistory("🤖 AI", aiReply);
  } catch (error) {
    console.error("❌ Fetch failed:", error);
    document.getElementById("responseBox").textContent = "发生错误，请稍后重试。";
  }
}

// 💬 Chat History
function addToHistory(sender, message) {
  const historyBox = document.getElementById("historyBox");
  conversationHistory.push({ sender, message });

  const entry = document.createElement("div");
  entry.innerHTML = `<strong>${sender}:</strong><br>${message}<hr>`;
  historyBox.appendChild(entry);
  historyBox.scrollTop = historyBox.scrollHeight;
}

// 📦 Bind file input to listener
document.getElementById("pdfFile").addEventListener("change", handleFileUpload);
