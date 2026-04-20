const state = {
  paperId: null,
};

const uploadForm = document.querySelector("#upload-form");
const paperFile = document.querySelector("#paper-file");
const paperStatus = document.querySelector("#paper-status");
const paperTitle = document.querySelector("#paper-title");
const paperLanguage = document.querySelector("#paper-language");
const chatForm = document.querySelector("#chat-form");
const chatInput = document.querySelector("#chat-input");
const selectedText = document.querySelector("#selected-text");
const messages = document.querySelector("#messages");

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = paperFile.files[0];
  if (!file) {
    addMessage("assistant", "请选择一篇 PDF。", "error");
    return;
  }

  setBusy(uploadForm, true);
  paperStatus.textContent = "上传中";
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/papers/upload", {
      method: "POST",
      body: formData,
    });
    const payload = await readJson(response);
    if (!response.ok) {
      throw new Error(payload.detail || "上传失败");
    }

    state.paperId = payload.paper_id;
    paperStatus.textContent = payload.status || "ready";
    paperTitle.textContent = payload.title || "未识别";
    paperLanguage.textContent = payload.language || "未知";
    addMessage("assistant", "论文已处理完成，可以开始提问。");
  } catch (error) {
    paperStatus.textContent = "失败";
    addMessage("assistant", error.message, "error");
  } finally {
    setBusy(uploadForm, false);
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!state.paperId) {
    addMessage("assistant", "请先上传一篇 PDF。", "error");
    return;
  }
  if (!message) {
    return;
  }

  addMessage("user", message);
  chatInput.value = "";
  setBusy(chatForm, true);

  try {
    const response = await fetch(`/api/papers/${state.paperId}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        selected_text: selectedText.value.trim() || null,
      }),
    });
    const payload = await readJson(response);
    if (!response.ok) {
      throw new Error(payload.detail || "请求失败");
    }
    addMessage("assistant", payload.answer, null, payload.citations || []);
  } catch (error) {
    addMessage("assistant", error.message, "error");
  } finally {
    setBusy(chatForm, false);
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    chatInput.value = button.dataset.prompt;
    chatInput.focus();
  });
});

function addMessage(role, text, variant = null, citations = []) {
  const article = document.createElement("article");
  article.className = `message message--${variant || role}`;

  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  article.appendChild(paragraph);

  if (citations.length) {
    const citationWrap = document.createElement("div");
    citationWrap.className = "citations";
    citations.forEach((citation) => {
      const item = document.createElement("span");
      item.className = "citation";
      item.textContent = formatCitation(citation);
      citationWrap.appendChild(item);
    });
    article.appendChild(citationWrap);
  }

  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

function formatCitation(citation) {
  const section = citation.section || "Unknown";
  const page =
    citation.page_start === citation.page_end
      ? `第 ${citation.page_start} 页`
      : `第 ${citation.page_start}-${citation.page_end} 页`;
  return `${section}，${page}`;
}

function setBusy(form, busy) {
  form.querySelectorAll("button, input, textarea").forEach((element) => {
    element.disabled = busy;
  });
}

async function readJson(response) {
  const text = await response.text();
  if (!text) {
    return {};
  }
  return JSON.parse(text);
}
