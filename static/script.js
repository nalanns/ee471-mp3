const outputImage = document.getElementById("output-image");
const imagePlaceholder = document.getElementById("image-placeholder");
const imageLoader = document.getElementById("image-loader");
const paintBtn = document.getElementById("paint-btn");
const promptInput = document.getElementById("prompt-input");
const chatHistory = document.getElementById("chat-history");
const micBtn = document.getElementById("mic-btn");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");

const messages = [];

async function postJSON(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || response.statusText);
  return data;
}

function addMessage(role, content) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  bubble.textContent = content;
  chatHistory.appendChild(bubble);
  chatHistory.scrollTop = chatHistory.scrollHeight;
  return bubble;
}

async function generateImage() {
  const prompt = promptInput.value.trim();
  if (!prompt || paintBtn.disabled) return;

  paintBtn.disabled = true;
  imageLoader.hidden = false;
  imagePlaceholder.hidden = true;

  try {
    const { image } = await postJSON("/api/generate", { prompt });
    outputImage.src = image;
    outputImage.hidden = false;
  } catch (error) {
    outputImage.hidden = true;
    imagePlaceholder.textContent = `Error: ${error.message}`;
    imagePlaceholder.hidden = false;
  } finally {
    imageLoader.hidden = true;
    paintBtn.disabled = false;
  }
}

async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || sendBtn.disabled) return;

  messageInput.value = "";
  messages.push({ role: "user", content: text });
  addMessage("user", text);
  const pending = addMessage("assistant", "Thinking...");
  pending.classList.add("pending");
  sendBtn.disabled = true;

  try {
    const { reply } = await postJSON("/api/chat", { messages });
    messages.push({ role: "assistant", content: reply });
    pending.textContent = reply;
  } catch (error) {
    messages.pop();
    pending.textContent = `Error: ${error.message}`;
    pending.classList.add("error");
  } finally {
    pending.classList.remove("pending");
    chatHistory.scrollTop = chatHistory.scrollHeight;
    sendBtn.disabled = false;
  }
}

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.onstart = () => micBtn.classList.add("listening");
  recognition.onend = () => micBtn.classList.remove("listening");
  recognition.onresult = (event) => {
    messageInput.value = Array.from(event.results)
      .map((result) => result[0].transcript)
      .join("");
  };
} else {
  micBtn.disabled = true;
  micBtn.title = "Speech recognition is not supported in this browser";
}

micBtn.addEventListener("click", () => {
  if (!recognition) return;
  if (micBtn.classList.contains("listening")) recognition.stop();
  else recognition.start();
});

paintBtn.addEventListener("click", generateImage);
sendBtn.addEventListener("click", sendMessage);

promptInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    generateImage();
  }
});

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") sendMessage();
});
