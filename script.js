pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.14.305/pdf.worker.min.js';
let uploadedPDF = null;
let conversationHistory = [];

function handleFileUpload() {
  const fileInput = document.getElementById('pdfFile');
  const file = fileInput.files[0];

  console.log("🟢 File selected:", file.name);

  if (!file || file.type !== 'application/pdf') {
    alert('请选择一个有效的 PDF 文件');
    return;
  }

  uploadedPDF = file;
  renderPDFPreview(file);
  document.getElementById('pdfPreview').innerHTML = '正在加载 PDF 预览...';
}

function clearFile() {
  uploadedPDF = null;
  document.getElementById('pdfFile').value = '';
  document.getElementById('pdfPreview').innerHTML = '请上传PDF文件以预览';
}

function renderPDFPreview(file) {
  const pdfPreview = document.getElementById('pdfPreview');
  const fileReader = new FileReader();

  fileReader.onload = function () {
    const typedArray = new Uint8Array(this.result);

    pdfjsLib.getDocument(typedArray).promise.then(pdf => {
      let pagesRendered = 0;
      pdfPreview.innerHTML = '';

      for (let pageNum = 1; pageNum <= Math.min(pdf.numPages, 3); pageNum++) {
        pdf.getPage(pageNum).then(page => {
          const scale = 1.2;
          const viewport = page.getViewport({ scale });
          const canvas = document.createElement('canvas');
          const context = canvas.getContext('2d');
          canvas.height = viewport.height;
          canvas.width = viewport.width;

          const renderContext = {
            canvasContext: context,
            viewport: viewport
          };

          page.render(renderContext).promise.then(() => {
            pdfPreview.appendChild(canvas);
            pagesRendered++;
            if (pagesRendered === Math.min(pdf.numPages, 3)) {
              console.log('PDF 预览完成');
            }
          });
        });
      }
    }).catch(error => {
      pdfPreview.innerHTML = '无法加载 PDF: ' + error.message;
    });
  };

  fileReader.readAsArrayBuffer(file);
}

async function submitQuestion() {
  const question = document.getElementById('questionInput').value.trim();
  if (!uploadedPDF) {
    alert('请先上传PDF文件');
    return;
  }
  if (!question) {
    alert('请输入问题');
    return;
  }

  // Append to history
  addToHistory('🧑‍🎓 学生', question);

  // Prepare form data
  const formData = new FormData();
  formData.append('file', uploadedPDF);
  formData.append('question', question);
  formData.append('history', JSON.stringify(conversationHistory));

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    const aiReply = result.answer || result.message || 'AI 没有返回答案';

    // Show response
    document.getElementById('responseBox').textContent = aiReply;

    // Save to history
    addToHistory('🤖 AI', aiReply);
  } catch (err) {
    console.error(err);
    document.getElementById('responseBox').textContent = '发生错误，请稍后重试。';
  }
}
document.getElementById("pdfFile").addEventListener("change", handleFileUpload);

function addToHistory(sender, message) {
  const historyBox = document.getElementById('historyBox');
  conversationHistory.push({ sender, message });

  const entry = document.createElement('div');
  entry.innerHTML = `<strong>${sender}:</strong><br>${message}<hr>`;
  historyBox.appendChild(entry);
  historyBox.scrollTop = historyBox.scrollHeight;
}
