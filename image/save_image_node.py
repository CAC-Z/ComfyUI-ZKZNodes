import os
import folder_paths
from PIL import Image
import numpy as np
from datetime import datetime
from datetime import date
import torch

class VrchSaveImageNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "base_save_path": ("STRING", {"default": "", "multiline": False}),
                "filename_prefix": ("STRING", {"default": "", "multiline": False}),
                "filename_suffix": ("STRING", {"default": "", "multiline": False}),
                "file_type": (["png", "jpg", "jpeg", "webp"],),
                "overwrite_if_exists": (["True","False"],),
                "folder_suffix": ("STRING", {"default": "", "multiline": False}),
                "use_date_folder": (["True","False"],{"default":"True"}),
                "use_date_in_filename": (["True", "False"], {"default": "False"}),
                "use_time_in_filename": (["True", "False"], {"default": "False"}),
             },
        }
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "save_image"
    CATEGORY = "ZKZ/Image"

    def save_image(self, image, base_save_path, filename_prefix, filename_suffix, file_type, overwrite_if_exists, folder_suffix, use_date_folder, use_date_in_filename, use_time_in_filename):
        # --- 路径构建部分 (保持不变) ---
        if base_save_path:
            real_base_path = base_save_path
        else:
             real_base_path = folder_paths.get_output_directory()

        if(use_date_folder=="True"):
            today = date.today()
            folder_name = today.strftime("%Y-%m-%d")
            if(folder_suffix!=""):
                folder_name=f"{folder_name}-{folder_suffix}"
            save_path = os.path.join(real_base_path, folder_name)
        else:
             save_path = real_base_path

        if not os.path.isdir(save_path):
            os.makedirs(save_path, exist_ok=True)

        file_type = file_type.lower()
            
        # --- 文件名构建逻辑 ---
        filename_parts = []
        if filename_prefix:
           filename_parts.append(str(filename_prefix))
        if use_date_in_filename == "True":
            filename_parts.append(date.today().strftime("%Y-%m-%d"))
        if use_time_in_filename == "True":
             filename_parts.append(datetime.now().strftime("%H-%M-%S"))
        if filename_suffix:
            filename_parts.append(str(filename_suffix))
        
        base_filename = "_".join(filename_parts)
        
        # --- 根据 base_filename 是否存在，决定命名策略 ---
        if base_filename:
            # --- 策略一：使用前缀/日期/时间命名 ---
            is_batch = len(image) > 1
            for i, single_image in enumerate(image):
                # 核心改动：仅在批处理时添加数字后缀
                if is_batch:
                    filename = f"{base_filename}_{i:04}"
                else:
                    filename = base_filename # 单张图片，直接使用前缀

                full_path = os.path.join(save_path, f"{filename}.{file_type}")
                
                # 现在覆盖逻辑能正确工作了
                if overwrite_if_exists == "False" and os.path.exists(full_path):
                    counter = 1
                    while True:
                        new_filename = f"{filename}_{counter:04}.{file_type}"
                        new_full_path = os.path.join(save_path, new_filename)
                        if not os.path.exists(new_full_path):
                            full_path = new_full_path
                            break
                        counter += 1
                
                # --- 图像转换和保存逻辑 ---
                img_tensor = single_image.unsqueeze(0)
                img_np = (img_tensor * 255).clamp(0, 255).to(torch.uint8).cpu().numpy()[0]
                if img_np.shape[2] == 1: img_np = np.squeeze(img_np, axis=-1)
                img_pil = Image.fromarray(img_np)
                img_pil.save(full_path)
                print(f"Saved image ({i+1}/{len(image)}) to: {full_path}")
        else:
            # --- 策略二：使用纯数字计数命名 (此逻辑保持不变) ---
            try:
                files = [f for f in os.listdir(save_path) if f.lower().endswith(f'.{file_type}')]
                numeric_files = [int(f.split('.')[0]) for f in files if f.split('.')[0].isdigit()]
                start_counter = max(numeric_files) + 1 if numeric_files else 0
            except Exception as e:
                print(f"扫描目录计数失败，从0开始。错误: {e}")
                start_counter = 0

            for i, single_image in enumerate(image):
                current_count = start_counter + i
                filename = f"{current_count:04}.{file_type}"
                full_path = os.path.join(save_path, filename)
                
                # --- 图像转换和保存逻辑 ---
                img_tensor = single_image.unsqueeze(0)
                img_np = (img_tensor * 255).clamp(0, 255).to(torch.uint8).cpu().numpy()[0]
                if img_np.shape[2] == 1: img_np = np.squeeze(img_np, axis=-1)
                img_pil = Image.fromarray(img_np)
                img_pil.save(full_path)
                print(f"Saved image ({i+1}/{len(image)}) to: {full_path}")

        return (image,)

NODE_CLASS_MAPPINGS = {
    "VrchSaveImageNode": VrchSaveImageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
     "VrchSaveImageNode": "保存图像",
}
