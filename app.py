import base64
import io
import threading
from functools import lru_cache
from pathlib import Path
from typing import Literal

import torch
from diffusers import AutoPipelineForText2Image
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

CHAT_MODEL_ID = "HuggingFaceTB/SmolLM2-360M-Instruct"
IMAGE_MODEL_ID = "stabilityai/sd-turbo"
SYSTEM_PROMPT = (
    "You are Dreamchat, a friendly assistant inside an image generation app. "
    "Keep answers short. When the user asks for an image prompt, reply with one "
    "vivid, detailed prompt of at most 40 words describing subject, style, lighting and colors."
)
STATIC_DIR = Path(__file__).parent / "static"

if torch.backends.mps.is_available():
    DEVICE = "mps"
elif torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"
DTYPE = torch.float32 if DEVICE == "cpu" else torch.float16

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
model_lock = threading.Lock()


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


class ImageRequest(BaseModel):
    prompt: str


@lru_cache(maxsize=1)
def load_chat_model():
    tokenizer = AutoTokenizer.from_pretrained(CHAT_MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(CHAT_MODEL_ID, torch_dtype=DTYPE).to(DEVICE)
    return tokenizer, model


@lru_cache(maxsize=1)
def load_image_pipeline():
    variant = "fp16" if DTYPE == torch.float16 else None
    pipe = AutoPipelineForText2Image.from_pretrained(IMAGE_MODEL_ID, torch_dtype=DTYPE, variant=variant)
    pipe = pipe.to(DEVICE)
    pipe.enable_attention_slicing()
    return pipe


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/chat")
def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
    conversation += [message.model_dump() for message in request.messages[-10:]]

    with model_lock:
        tokenizer, model = load_chat_model()
        inputs = tokenizer.apply_chat_template(
            conversation, add_generation_prompt=True, return_tensors="pt", return_dict=True
        ).to(DEVICE)
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=200,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
            )

    reply = tokenizer.decode(output[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True).strip()
    return {"reply": reply}


@app.post("/api/generate")
def generate(request: ImageRequest):
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is empty")

    with model_lock:
        pipe = load_image_pipeline()
        image = pipe(
            prompt=prompt,
            num_inference_steps=4,
            guidance_scale=0.0,
            height=512,
            width=512,
        ).images[0]

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return {"image": f"data:image/png;base64,{encoded}"}
