import torch
import numpy as np
from PIL import Image

class VrchIsolateColorNode:  # 类名改为更贴切的名称
    CATEGORY = "ZKZ"
    RETURN_TYPES = ("IMAGE",)
    OUTPUT_NODE = True
    FUNCTION = "isolate_color" # 函数名也修改

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "isolate_color": (["Black", "White"],), # 输入参数名更明确
                "threshold": ("INT", {"default": 50, "min": 0, "max": 255, "step": 1}),
            }
        }

    def isolate_color(self, image, isolate_color, threshold): # 函数名也修改
        """
        隔离图像中指定颜色以外的区域，将指定颜色区域变为透明。

        Args:
            image: ComfyUI Image tensor.
            isolate_color: "Black" 或 "White"，选择要隔离的颜色区域。
            threshold: 颜色阈值。

        Returns:
            torch.Tensor: 处理后的 ComfyUI Image tensor.
        """
        batch_size = image.shape[0]
        output_images = []

        for b in range(batch_size):
            img_np = image[b].cpu().numpy()
            img_pil = Image.fromarray((img_np * 255).astype(np.uint8)).convert("RGBA")
            pixels = img_pil.load()

            for x in range(img_pil.width):
                for y in range(img_pil.height):
                    r, g, b, a = pixels[x, y]

                    is_target_color = False # 标记是否为目标颜色 (黑色或白色)
                    if isolate_color == "Black":
                        if max(r, g, b) < threshold: # 使用改进后的黑色判断
                            is_target_color = True
                    elif isolate_color == "White":
                        if min(r, g, b) > 255 - threshold: # 使用改进后的白色判断
                            is_target_color = True

                    if is_target_color:
                        pixels[x, y] = (0, 0, 0, 0)  # RGBA: 透明  (如果是目标颜色，则透明)
                    else:
                        pass # 如果不是目标颜色，保持原样

            output_img_np = np.array(img_pil).astype(np.float32) / 255.0
            output_images.append(torch.from_numpy(output_img_np).unsqueeze(0))

        output_tensor = torch.cat(output_images, dim=0)
        return (output_tensor,)


NODE_CLASS_MAPPINGS = {
    "VrchIsolateColorNode": VrchIsolateColorNode, # 类名和映射名更新
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VrchIsolateColorNode": "隔离颜色（黑/白）", # 显示名称更新
}