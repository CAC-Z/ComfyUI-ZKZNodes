import base64
import io
import os
import requests
import numpy as np
from PIL import Image


ARK_CHAT_DEFAULT_URL = "https://ark.cn-beijing.volces.com/api/v3/responses"
ARK_CHAT_COMPLETIONS_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"


def _use_chat_completions(resolved_url, model):
    if "chat/completions" in resolved_url:
        return True
    return model.startswith("doubao-1-5-vision")


def _extract_text(response_json):
    if "choices" in response_json:
        choice = response_json["choices"][0]
        message = choice.get("message", {})
        if "content" in message:
            content = message["content"]
            if isinstance(content, list):
                text_chunks = []
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        text_chunks.append(item["text"])
                if text_chunks:
                    return "\n".join(text_chunks)
            return content
    if "output" in response_json:
        chunks = []
        for item in response_json.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text" and "text" in content:
                    chunks.append(content["text"])
        if chunks:
            return "\n".join(chunks)
        raise ValueError(
            "No output_text in response. Try increasing max_output_tokens or disabling thinking in the model settings."
        )
    raise ValueError(f"Unexpected response: {response_json}")


class ArkChatText:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "system_prompt": ("STRING", {"multiline": True, "default": "你是人工智能助手"}),
                "input_text": ("STRING", {"multiline": True, "default": ""}),
                "model": ("STRING", {"multiline": False, "default": "doubao-seed-1-8-251228"}),
                "max_output_tokens": ("INT", {"default": 1024, "min": 1}),
                "thinking": ("BOOLEAN", {"default": True}),
                "api_key": ("STRING", {"multiline": False, "default": ""}),
                "api_url": ("STRING", {"multiline": False, "default": ""}),
            },
            "optional": {
                "image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"
    CATEGORY = "ZKZ/API"

    def run(self, input_text, system_prompt, model, max_output_tokens, thinking, api_key, api_url, image=None):
        resolved_key = api_key.strip() or os.environ.get("ARK_API_KEY", "").strip()
        if not resolved_key:
            raise ValueError("Missing API key. Set api_key or ARK_API_KEY.")

        resolved_url = api_url.strip() or os.environ.get("ARK_API_URL", "").strip() or ARK_CHAT_DEFAULT_URL
        use_chat_completions = _use_chat_completions(resolved_url, model)
        if not api_url.strip() and use_chat_completions:
            resolved_url = ARK_CHAT_COMPLETIONS_URL

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {resolved_key}",
        }
        content_items = []
        if image is not None:
            if len(image.shape) > 3:
                image = image[0]
            img_np = (255.0 * image.cpu().numpy()).clip(0, 255).astype(np.uint8)
            pil_img = Image.fromarray(img_np)
            buffer = io.BytesIO()
            pil_img.save(buffer, format="JPEG", quality=90)
            img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            content_items.append(
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{img_b64}",
                }
            )
        content_items.append(
            {
                "type": "input_text",
                "text": input_text,
            }
        )

        if use_chat_completions:
            message_content = []
            if image is not None:
                message_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": content_items[0]["image_url"]},
                    }
                )
            message_content.append({"type": "text", "text": input_text})
            thinking_mode = "enabled" if thinking else "disabled"
            payload = {
                "model": model,
                "max_tokens": max_output_tokens,
                "thinking": {"type": thinking_mode},
                "messages": [
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": system_prompt,
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": message_content,
                    },
                ],
            }
        else:
            input_messages = []
            if system_prompt.strip():
                input_messages.append(
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "input_text",
                                "text": system_prompt,
                            }
                        ],
                    }
                )
            input_messages.append(
                {
                    "role": "user",
                    "content": content_items,
                }
            )

            payload = {
                "model": model,
                "max_output_tokens": max_output_tokens,
                "thinking": {"type": "enabled" if thinking else "disabled"},
                "input": input_messages,
            }

        res = requests.post(resolved_url, json=payload, headers=headers, timeout=180)
        try:
            res.raise_for_status()
        except requests.HTTPError as exc:
            detail = res.text.strip()
            raise ValueError(f"HTTP {res.status_code} error: {detail}") from exc
        data = res.json()
        text = _extract_text(data)

        return (text,)


NODE_CLASS_MAPPINGS = {
    "ArkChatText": ArkChatText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArkChatText": "火山引擎 LLM",
}
