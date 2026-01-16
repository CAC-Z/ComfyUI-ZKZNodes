import os
import torch
from PIL import Image
import numpy as np
from datetime import datetime, date
import folder_paths

class ConditionalSaveImageNode:
    CATEGORY = "ZKZ/Image"

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE", ),
                "condition": ("STRING", {"default": "0", "multiline": False}),
                "base_save_path": ("STRING", {"default": "", "multiline": False}),
                "filename_prefix": ("STRING", {"default": "", "multiline": False}),
                "filename_suffix": ("STRING", {"default": "", "multiline": False}),
                "file_type": (["png", "jpg", "jpeg", "webp"],),
                "overwrite_if_exists": (["True","False"],),
                "folder_suffix": ("STRING", {"default": "", "multiline": False}),
                "use_date_folder": (["True","False"],{"default":"True"}),
                "use_date_in_filename": (["True", "False"], {"default": "False"}),
                "use_time_in_filename": (["True", "False"], {"default": "False"}),
            }
        }

    FUNCTION = "execute"

    def execute(self, image, condition, base_save_path, filename_prefix, filename_suffix, file_type, overwrite_if_exists, folder_suffix, use_date_folder, use_date_in_filename, use_time_in_filename):
        if condition == "1":
            if not base_save_path:
                save_path = folder_paths.get_output_directory()  # Use ComfyUI's output directory if base_save_path is empty
            else:
                real_base_path = base_save_path


            if(use_date_folder=="True"):
                today = date.today()
                folder_name = today.strftime("%Y-%m-%d")
                if(folder_suffix!=""):
                    folder_name=f"{folder_name}-{folder_suffix}"

                save_path = os.path.join(real_base_path, folder_name)
            else:
                 save_path = real_base_path

            if not os.path.isdir(save_path):
                os.makedirs(save_path,exist_ok=True)

            file_type = file_type.lower()

            filename_parts = []

            if filename_prefix:
               filename_parts.append(filename_prefix)

            if use_date_in_filename == "True":
                filename_parts.append(date.today().strftime("%Y-%m-%d"))

            if use_time_in_filename == "True":
                 filename_parts.append(datetime.now().strftime("%H-%M-%S"))

            if filename_suffix:
                filename_parts.append(filename_suffix)

            base_filename = "_".join(filename_parts) if filename_parts else "image" # Default filename if no prefix/suffix

            i = 1
            while True:
                if i > 1:
                    filename = f"{base_filename}_{i-1:04}.{file_type}" if base_filename != "image" else f"{i-1:04}.{file_type}" # Add counter only if needed for non-overwrite
                else:
                    filename = f"{base_filename}.{file_type}" if base_filename != "image" else f"image.{file_type}" # No counter for the first try

                full_path = os.path.join(save_path, filename)

                if overwrite_if_exists=="True" or not os.path.exists(full_path):
                    break

                if overwrite_if_exists=="False":
                    i += 1
                else:
                    break # If overwrite is true, we only try once and overwrite


            img = (image * 255).clamp(0, 255).to(torch.uint8)
            img = img.cpu().numpy()

            if img.ndim==4: # Remove batch dimension
                  img = img[0]

            # Improved shape handling
            if img.ndim == 3: # Potential RGB or other multi-channel
                if img.shape[2] == 1:  # Grayscale image with trailing channel
                    img = np.squeeze(img, axis=-1)  # Remove trailing channel
                elif img.shape[0] == 1 or img.shape[1] == 1: #Handle cases like (1, H, W) or (H, 1, W)
                    img = np.squeeze(img) #Remove the dimension of size 1 if any
            elif img.ndim > 3:
                raise ValueError(f"Unexpected image dimensions: {img.shape}") # Raise error if dimension is still greater than 3

            img = Image.fromarray(img)
            img.save(full_path)

            print(f"Saved image to: {full_path}")
        return (image,)

NODE_CLASS_MAPPINGS = {
    "ConditionalSaveImageNode": ConditionalSaveImageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ConditionalSaveImageNode": "条件保存图像",
}
