import torch
import numpy as np
from PIL import Image
import cv2
import torch.nn.functional as F

class ImageSplitterByTransparency:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "min_width": ("INT", {"default": 150, "min": 1, "max": 8192, "step": 1, "display": "number"}),
                "min_height": ("INT", {"default": 150, "min": 1, "max": 8192, "step": 1, "display": "number"}),
                # 新增：Alpha阈值参数，用于控制分割灵敏度
                "alpha_threshold": ("INT", {"default": 80, "min": 0, "max": 255, "step": 1, "display": "slider"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "split_image"
    CATEGORY = "ZKZ/Image" # 与你的保存节点保持一致的分类

    # 更新函数定义以接收新参数
    def split_image(self, image, min_width, min_height, alpha_threshold):
        # 用于存储所有从批次中分割出来的、符合条件的图像块 (Tensor格式)
        processed_parts = []

        # ComfyUI的输入是一个批次, 即使只有一张图, 也要遍历
        for single_image_tensor in image:
            # 1. 将输入的Tensor (0-1范围, float) 转换为NumPy数组 (0-255范围, uint8)
            img_np = np.clip(255. * single_image_tensor.cpu().numpy(), 0, 255).astype(np.uint8)
            
            # 确保图像有Alpha通道
            if img_np.shape[2] != 4:
                pil_img = Image.fromarray(img_np).convert("RGBA")
                img_np = np.array(pil_img)

            # 2. 使用你的核心分割逻辑
            # 如果图像完全透明，则跳过
            if np.all(img_np[:, :, 3] == 0):
                continue

            alpha_channel = img_np[:, :, 3]
            # 修改：使用可调节的alpha_threshold替换固定的15
            _, thresh = cv2.threshold(alpha_channel, alpha_threshold, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                continue

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                if w < min_width or h < min_height:
                    continue

                cropped_img_np = img_np[y:y+h, x:x+w]
                
                cropped_tensor = torch.from_numpy(cropped_img_np.astype(np.float32) / 255.0)
                processed_parts.append(cropped_tensor)

        if not processed_parts:
            return (torch.zeros((1, 1, 1, 4)),)

        max_h = max(part.shape[0] for part in processed_parts)
        max_w = max(part.shape[1] for part in processed_parts)

        padded_parts = []
        for part in processed_parts:
            h, w, c = part.shape
            pad_h_top = (max_h - h) // 2
            pad_h_bottom = max_h - h - pad_h_top
            pad_w_left = (max_w - w) // 2
            pad_w_right = max_w - w - pad_w_left
            
            padding = (pad_w_left, pad_w_right, pad_h_top, pad_h_bottom)
            padded_part = F.pad(part.permute(2, 0, 1), padding, "constant", 0).permute(1, 2, 0)
            padded_parts.append(padded_part)

        final_batch = torch.stack(padded_parts)

        return (final_batch,)

# --- ComfyUI 注册 ---
NODE_CLASS_MAPPINGS = {
    "ImageSplitterByTransparency": ImageSplitterByTransparency
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageSplitterByTransparency": "图像透明分割"
}
