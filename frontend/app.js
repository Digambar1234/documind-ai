const API_BASE =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? ""
    : "https://documind-ai-sxog.onrender.com";

const uploadForm = document.querySelector("#uploadForm");
const fileInput = document.querySelector("#fileInput");
const chooseFileButton = document.querySelector("#chooseFileButton");
const fileName = document.querySelector("#fileName");
const fileHint = document.querySelector("#fileHint");
const uploadButton = document.querySelector("#uploadButton");
const uploadStatus = document.querySelector("#uploadStatus");
const indexedFile = document.querySelector("#indexedFile");
const chunkCount = document.querySelector("#chunkCount");
const sourceCount = document.querySelector("#sourceCount");
const queryCount = document.querySelector("#queryCount");
const chatForm = document.querySelector("#chatForm");
const questionInput = document.querySelector("#questionInput");
const askButton = document.querySelector("#askButton");
const messages = document.querySelector("#messages");
const clearButton = document.querySelector("#clearButton");
const canvas = document.querySelector("#vectorCanvas");
const canvasContext = canvas?.getContext("2d");

let totalQueries = 0;
let latestSourceCount = 0;
let vectorAnimationFrame = null;

chooseFileButton.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  syncSelectedFile();
});

["dragenter", "dragover"].forEach((eventName) => {
  chooseFileButton.addEventListener(eventName, (event) => {
    event.preventDefault();
    chooseFileButton.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  chooseFileButton.addEventListener(eventName, (event) => {
    event.preventDefault();
    chooseFileButton.classList.remove("dragging");
  });
});

chooseFileButton.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (!file) return;

  fileInput.files = event.dataTransfer.files;
  syncSelectedFile();
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = fileInput.files[0];

  if (!file) return;

  setStatus("Indexing", "");
  uploadButton.disabled = true;

  const body = new FormData();
  body.append("file", file);

  try {
    const response = await fetch(`${API_BASE}/api/documents/upload`, {
      method: "POST",
      body,
    });
    const data = await parseResponse(response);

    indexedFile.textContent = data.file_name;
    chunkCount.textContent = `${data.chunks_created} chunks indexed via ${formatExtractionMethod(data.extraction_method)}`;
    setStatus("Indexed", "success");
  } catch (error) {
    setStatus("Failed", "error");
    addAssistantMessage(error.message, []);
  } finally {
    uploadButton.disabled = false;
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();

  if (!question) return;

  clearEmptyState();
  addUserMessage(question);
  questionInput.value = "";
  askButton.disabled = true;
  askButton.textContent = "Thinking";

  try {
    const response = await fetch(`${API_BASE}/api/chat/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });
    const data = await parseResponse(response);
    totalQueries += 1;
    latestSourceCount = data.sources?.length || 0;
    updateMetrics();
    addAssistantMessage(data.answer, data.sources || []);
  } catch (error) {
    addAssistantMessage(error.message, []);
  } finally {
    askButton.disabled = false;
    askButton.textContent = "Ask";
  }
});

clearButton.addEventListener("click", () => {
  messages.innerHTML = `
    <div class="empty-state">
      <span class="empty-icon">
        <svg viewBox="0 0 40 40" aria-hidden="true">
          <path d="M7 8h15l7 7v17H7z" />
          <path d="M22 8v8h7M12 22h12M12 27h8" />
        </svg>
      </span>
      <h2>Your document answers will appear here.</h2>
      <p>Try asking: "What is this document about?"</p>
    </div>
  `;
});

function addUserMessage(text) {
  addMessage("You", text, "user");
}

function addAssistantMessage(text, sources) {
  const node = addMessage("DocuMind", text, "assistant");

  if (sources.length > 0) {
    const sourceToggle = document.createElement("button");
    sourceToggle.className = "source-toggle";
    sourceToggle.type = "button";
    sourceToggle.textContent = `Show ${sources.length} source${sources.length === 1 ? "" : "s"}`;

    const sourceList = document.createElement("div");
    sourceList.className = "sources";
    sourceList.hidden = true;

    sources.forEach((source, index) => {
      const item = document.createElement("article");
      item.className = "source";

      const header = document.createElement("div");
      header.className = "source-header";
      header.innerHTML = `<span>${escapeHtml(source.file_name || "Unknown")}</span><span>Page ${escapeHtml(String(source.page ?? "N/A"))}</span>`;

      const chunk = document.createElement("pre");
      chunk.textContent = source.content_preview || "";

      item.append(header, chunk);
      sourceList.append(item);

      if (index === 0) {
        item.setAttribute("aria-label", "Top source");
      }
    });

    sourceToggle.addEventListener("click", () => {
      sourceList.hidden = !sourceList.hidden;
      sourceToggle.textContent = sourceList.hidden
        ? `Show ${sources.length} source${sources.length === 1 ? "" : "s"}`
        : "Hide sources";
    });

    node.append(sourceToggle, sourceList);
  }

  messages.scrollTop = messages.scrollHeight;
}

function addMessage(label, text, type) {
  clearEmptyState();

  const node = document.createElement("article");
  node.className = `message ${type}`;

  const labelNode = document.createElement("div");
  labelNode.className = "message-label";
  labelNode.textContent = label;

  const textNode = document.createElement("p");
  textNode.textContent = text;

  node.append(labelNode, textNode);
  messages.append(node);
  messages.scrollTop = messages.scrollHeight;
  return node;
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (response.ok) {
    return data;
  }

  const detail = typeof data === "object" && data !== null ? data.detail : data;
  throw new Error(detail || "Request failed.");
}

function clearEmptyState() {
  const emptyState = messages.querySelector(".empty-state");
  if (emptyState) {
    emptyState.remove();
  }
}

function setStatus(text, state) {
  uploadStatus.innerHTML = `<span></span>${escapeHtml(text)}`;
  uploadStatus.className = `status ${state}`.trim();
}

function syncSelectedFile() {
  const file = fileInput.files[0];
  uploadButton.disabled = !file;

  if (!file) {
    fileName.textContent = "Choose a PDF";
    fileHint.textContent = "Drop a company PDF here or browse";
    return;
  }

  const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
  fileName.textContent = file.name;
  fileHint.textContent = isPdf ? `${formatBytes(file.size)} selected` : "Please choose a PDF file";
  uploadButton.disabled = !isPdf;
}

function updateMetrics() {
  sourceCount.textContent = latestSourceCount;
  queryCount.textContent = totalQueries;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatExtractionMethod(method) {
  if (method === "gemini_ocr") return "Gemini OCR";
  return "PDF text";
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function drawVectorCanvas() {
  if (!canvasContext || !canvas) return;
  if (vectorAnimationFrame) {
    cancelAnimationFrame(vectorAnimationFrame);
  }

  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.floor(rect.width * ratio);
  canvas.height = Math.floor(rect.height * ratio);
  canvasContext.setTransform(ratio, 0, 0, ratio, 0, 0);

  const points = Array.from({ length: 48 }, (_, index) => ({
    x: (index * 97) % Math.max(rect.width, 1),
    y: (index * 53) % Math.max(rect.height, 1),
    r: 1.4 + (index % 4) * 0.45,
    speed: 0.25 + (index % 5) * 0.08,
  }));

  function frame(time) {
    canvasContext.clearRect(0, 0, rect.width, rect.height);
    canvasContext.fillStyle = "rgba(255,255,255,0.78)";
    canvasContext.strokeStyle = "rgba(213,168,79,0.18)";
    canvasContext.lineWidth = 1;

    points.forEach((point, index) => {
      point.y += point.speed;
      point.x += Math.sin(time / 900 + index) * 0.28;
      if (point.y > rect.height + 8) point.y = -8;

      canvasContext.beginPath();
      canvasContext.arc(point.x, point.y, point.r, 0, Math.PI * 2);
      canvasContext.fill();

      for (let next = index + 1; next < points.length; next += 1) {
        const other = points[next];
        const distance = Math.hypot(point.x - other.x, point.y - other.y);
        if (distance < 82) {
          canvasContext.globalAlpha = (82 - distance) / 180;
          canvasContext.beginPath();
          canvasContext.moveTo(point.x, point.y);
          canvasContext.lineTo(other.x, other.y);
          canvasContext.stroke();
          canvasContext.globalAlpha = 1;
        }
      }
    });

    drawDocumentStack(rect.width, rect.height, time);
    vectorAnimationFrame = requestAnimationFrame(frame);
  }

  vectorAnimationFrame = requestAnimationFrame(frame);
}

function drawDocumentStack(width, height, time) {
  const centerX = width / 2;
  const centerY = height / 2;
  const float = Math.sin(time / 700) * 5;

  canvasContext.save();
  canvasContext.translate(centerX, centerY + float);
  canvasContext.rotate(-0.07);

  [
    { x: -72, y: -44, color: "rgba(255,255,255,0.18)" },
    { x: -54, y: -56, color: "rgba(255,255,255,0.26)" },
    { x: -36, y: -68, color: "rgba(255,255,255,0.34)" },
  ].forEach((sheet) => {
    canvasContext.fillStyle = sheet.color;
    roundRect(canvasContext, sheet.x, sheet.y, 118, 150, 8);
    canvasContext.fill();
    canvasContext.strokeStyle = "rgba(255,255,255,0.22)";
    canvasContext.stroke();
  });

  canvasContext.fillStyle = "rgba(213,168,79,0.9)";
  roundRect(canvasContext, 1, -28, 74, 8, 4);
  canvasContext.fill();
  canvasContext.fillStyle = "rgba(255,255,255,0.78)";
  roundRect(canvasContext, 1, -6, 92, 6, 3);
  canvasContext.fill();
  roundRect(canvasContext, 1, 12, 68, 6, 3);
  canvasContext.fill();

  canvasContext.restore();
}

function roundRect(context, x, y, width, height, radius) {
  context.beginPath();
  context.moveTo(x + radius, y);
  context.arcTo(x + width, y, x + width, y + height, radius);
  context.arcTo(x + width, y + height, x, y + height, radius);
  context.arcTo(x, y + height, x, y, radius);
  context.arcTo(x, y, x + width, y, radius);
  context.closePath();
}

drawVectorCanvas();
window.addEventListener("resize", drawVectorCanvas);
