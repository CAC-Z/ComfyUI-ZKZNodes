import base64
import io
import os

import requests
import torch
import numpy as np
from PIL import Image


ARK_DEFAULT_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
ASPECT_RATIO_TO_SIZE = {
    "1:1": "2048x2048",
    "4:3": "2304x1728",
    "3:4": "1728x2304",
    "16:9": "2560x1440",
    "9:16": "1440x2560",
    "3:2": "2496x1664",
    "2:3": "1664x2496",
    "21:9": "3024x1296",
}


def _pil_to_tensor(pil_img):
    img_np = np.array(pil_img).astype(np.float32) / 255.0
    return torch.from_numpy(img_np)


def _load_image_from_url(url):
    res = requests.get(url, timeout=120)
    res.raise_for_status()
    return Image.open(io.BytesIO(res.content)).convert("RGB")


class Seedream45Generate:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "aspect_ratio": (list(ASPECT_RATIO_TO_SIZE.keys()),),
                "model": ("STRING", {"multiline": False, "default": "doubao-seedream-4-5-251128"}),
                "api_key": ("STRING", {"multiline": False, "default": ""}),
                "api_url": ("STRING", {"multiline": False, "default": ""}),
                "watermark": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "run"
    CATEGORY = "ZKZ/API"

    def run(self, prompt, aspect_ratio, model, api_key, api_url, watermark):
        resolved_key = api_key.strip() or os.environ.get("ARK_API_KEY", "").strip()
        if not resolved_key:
            raise ValueError("Missing API key. Set api_key or ARK_API_KEY.")

        resolved_url = api_url.strip() or os.environ.get("ARK_API_URL", "").strip() or ARK_DEFAULT_URL
        size = ASPECT_RATIO_TO_SIZE.get(aspect_ratio)
        if not size:
            raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {resolved_key}",
        }
        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "watermark": watermark,
        }

        res = requests.post(resolved_url, json=payload, headers=headers, timeout=180)
        res.raise_for_status()
        data = res.json()

        if "data" not in data or not data["data"]:
            raise ValueError(f"Unexpected response: {data}")

        images = []
        for item in data["data"]:
            if "b64_json" in item and item["b64_json"]:
                img_bytes = base64.b64decode(item["b64_json"])
                pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                images.append(_pil_to_tensor(pil_img))
            elif "url" in item and item["url"]:
                pil_img = _load_image_from_url(item["url"])
                images.append(_pil_to_tensor(pil_img))

        if not images:
            raise ValueError(f"No images returned: {data}")

        return (torch.stack(images),)


NODE_CLASS_MAPPINGS = {
    "Seedream45Generate": Seedream45Generate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Seedream45Generate": "火山引擎 图像生成",
}
