import torch
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import os
import folder_paths

class LoadRGBALocalOrURL:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_path_or_url": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "URL或本地路径，支持PNG透明图像"
                })
            },
            "optional": {
                # ComfyUI使用BOOLEAN而不是具体的上传组件类型
                "local_file": ("BOOLEAN", {"default": False, "label": "从本地文件加载"})
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image_rgba", "mask_alpha")
    FUNCTION = "load_image_main"
    CATEGORY = "ZKZ/Image"

    def _empty_result(self):
        image_tensor_rgba = torch.zeros((1, 1, 1, 4), dtype=torch.float32)
        mask_tensor_alpha = torch.zeros((1, 1, 1), dtype=torch.float32)
        return (image_tensor_rgba, mask_tensor_alpha)

    def load_image_main(self, image_path_or_url, local_file=False):
        pil_image = None
        source_info = "unknown source"

        if not image_path_or_url or not image_path_or_url.strip():
            print("错误: 未提供图像路径或URL")
            return self._empty_result()

        path = image_path_or_url.strip()
        source_info = f"路径/URL: {path}"

        try:
            if path.startswith("http://") or path.startswith("https://"):
                # 从URL加载
                response = requests.get(path, timeout=20)
                response.raise_for_status()
                img_bytes = BytesIO(response.content)
                pil_image = Image.open(img_bytes).convert("RGBA")
                print(f"成功从URL加载图像: {path}")
            else:
                # 从本地路径加载
                resolved_path = path
                if local_file:
                    # 如果是相对路径，尝试在ComfyUI的输入目录中查找
                    if not os.path.isabs(path):
                        input_dir = folder_paths.get_input_directory()
                        possible_path = os.path.join(input_dir, path)
                        if os.path.exists(possible_path):
                            resolved_path = possible_path
                
                if not os.path.exists(resolved_path):
                    # 尝试使用ComfyUI的路径解析
                    try:
                        resolved_path = folder_paths.get_annotated_filepath(path)
                    except:
                        pass
                
                if not os.path.exists(resolved_path):
                    print(f"错误: 找不到图像文件 '{path}'")
                    return self._empty_result()
                
                pil_image = Image.open(resolved_path).convert("RGBA")
                print(f"成功从本地加载图像: {resolved_path}")
        except Exception as e:
            print(f"加载图像时出错: {e}")
            return self._empty_result()

        if pil_image is None:
            print(f"错误: 无法从{source_info}加载图像。")
            return self._empty_result()

        # 转换为张量
        out_image_np = np.array(pil_image, dtype=np.float32) / 255.0
        image_tensor_rgba = torch.from_numpy(out_image_np)[None,]
        # 提取alpha通道作为mask
        mask_tensor_alpha = image_tensor_rgba[:, :, :, 3].clone()

        print(f"图像加载成功，形状: {image_tensor_rgba.shape}，包含透明通道")
        return (image_tensor_rgba, mask_tensor_alpha)

# 添加节点映射
NODE_CLASS_MAPPINGS = {
    "LoadRGBALocalOrURL": LoadRGBALocalOrURL
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadRGBALocalOrURL": "加载透明PNG图像"
}
