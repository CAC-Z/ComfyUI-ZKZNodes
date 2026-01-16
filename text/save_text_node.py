import os
from datetime import datetime

import folder_paths


class ZKZSaveTextNode:
    """
    保存字符串到 txt 文件的简单节点。
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_content": ("STRING", {"default": "", "multiline": True}),
                "base_save_path": ("STRING", {"default": "", "multiline": False}),
                "filename_prefix": ("STRING", {"default": "", "multiline": False}),
                "filename_separator": ("STRING", {"default": "", "multiline": False}),
                "filename_zero_padding": ("INT", {"default": 0, "min": 0, "max": 8}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "save_text"
    CATEGORY = "ZKZ/Text"

    def save_text(
        self,
        text_content,
        base_save_path,
        filename_prefix,
        filename_separator,
        filename_zero_padding,
    ):
        text = text_content if isinstance(text_content, str) else str(text_content)
        base_path = base_save_path.strip() or folder_paths.get_output_directory()
        os.makedirs(base_path, exist_ok=True)

        prefix = filename_prefix.strip() or "text"
        separator = filename_separator or ""
        padding = max(0, int(filename_zero_padding or 0))

        def build_name(counter):
            if padding > 0:
                digit = str(counter).zfill(padding)
                return f"{prefix}{separator}{digit}" if separator else f"{prefix}{digit}"
            if counter == 0:
                return prefix
            return f"{prefix}{separator}{counter}" if separator else f"{prefix}{counter}"

        counter = 0
        while True:
            candidate = os.path.join(base_path, f"{build_name(counter)}.txt")
            if not os.path.exists(candidate):
                target_path = candidate
                break
            counter += 1

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"[ZKZ Save Text] Saved text ({len(text)} chars) to: {target_path}")
        return (text,)


NODE_CLASS_MAPPINGS = {
    "ZKZSaveTextNode": ZKZSaveTextNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZKZSaveTextNode": "保存文本",
}
