# Dreamchat — EE 471 Mini Project 3

A simple web app that generates images from text prompts and chats with a small LLM by voice or text.

- **Image generation:** [stabilityai/sd-turbo](https://huggingface.co/stabilityai/sd-turbo) (4 steps, 512×512)
- **Chatbot:** [HuggingFaceTB/SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct)
- **Speech-to-text:** browser Web Speech API
- **Backend:** FastAPI · **Frontend:** HTML, CSS, JavaScript

Figma design: https://www.figma.com/design/9PfMbnVk3jnSwytpBjM7p5/Untitled?node-id=0-1&t=CoQfMRBbquQZ7twD-1

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --port 8000
```

Open http://localhost:8000 in Chrome. The first image and first chat message download the models (~3 GB total), so they take longer.

## Usage

1. Press the mic button, speak, then press send. Your message and the bot's reply appear in the chat history.
2. Ask the bot for an image prompt, copy it into the prompt box, and press the paint button.
