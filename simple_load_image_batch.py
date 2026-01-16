import os
import glob
import json
from PIL import Image, ImageOps
import torch
import numpy as np
import time
import re
import folder_paths

def natural_sort_key(s):

    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

class ValidatePath:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path_string": ("STRING", {"default": "", "multiline": False}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("path",)
    FUNCTION = "validate"
    CATEGORY = "ZKZ/Utils"

    def validate(self, path_string):
        if not path_string:
            print("Warning: Input path is empty.")
            return ("",)
        if not os.path.exists(path_string):
            print(f"Warning: Path '{path_string}' does not exist.")
            return ("",)
        return (os.path.abspath(path_string),)

ALLOWED_EXT = {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}
TEXT_TYPE = "STRING"


class SimpleDB:
    def __init__(self):
        base_dir = os.path.dirname(os.path.realpath(__file__))
        self.db_path = os.path.join(base_dir, "batch_counter.json")
        self.load_db()

    def load_db(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except:
                self.data = {}
        else:
            self.data = {}

    def save_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f)

    def get(self, key, default=0):
        return self.data.get(key, default)

    def insert(self, key, value):
        self.data[key] = value
        self.save_db()


def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


class Simple_Load_Image_Batch:
    # (这个类的其他部分没有变化，所以省略了)
    def __init__(self):
        self.db = SimpleDB()
        self.loader = None
        self.prev_loop = None
        self.prev_reset = 0
        self.prev_allow_RGBA_output = None
        self.prev_path = None
        self.prev_pattern = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path": ("STRING", {"default": '', "multiline": False}),
                "pattern": ("STRING", {"default": '*', "multiline": False}),
                "loop": (["true", "false"], {"default": "true"}),
                "allow_RGBA_output": (["false", "true"], {"default": "false"}),
                "reset": ("INT", {"default": 0, "min": 0, "max": 1, "step": 1}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", TEXT_TYPE, "STRING", "STRING")
    RETURN_NAMES = ("image", "mask", "filename_text", "text", "total_images")
    FUNCTION = "load_batch_images"
    CATEGORY = "ZKZ"

    def load_batch_images(self, path, pattern='*', loop="true", allow_RGBA_output='false', reset=0):
        if not path or not os.path.exists(path):
            print(f"Load Image Batch: Path '{path}' is invalid or does not exist. Halting execution.")
            return (None, None, None, None, None)

        directory_mtime = self.get_directory_mtime(path)

        recreate_loader = (
                self.loader is None
                or self.loader.key != f"{path}|{pattern}"
                or self.prev_loop != loop
                or reset != self.prev_reset
                or self.loader.mtime != directory_mtime
                or self.prev_allow_RGBA_output != allow_RGBA_output
                or self.prev_path != path
                or self.prev_pattern != pattern
        )

        if recreate_loader:
            if self.loader is not None and self.prev_loop == "true" and loop == "false":
                self.db.insert(self.loader.key + "_temp_index", self.loader.index)

            self.loader = BatchImageLoader(path, pattern, self.db)

            if self.prev_loop == "true" and loop == "false":
                self.loader.index = self.db.get(self.loader.key + "_temp_index", 0)
                self.loader.end_reached = False

            if loop == "false" and reset != self.prev_reset:
                self.loader.index = 0
                self.loader.end_reached = False

        self.prev_loop = loop
        self.prev_reset = reset
        self.prev_allow_RGBA_output = allow_RGBA_output
        self.prev_path = path
        self.prev_pattern = pattern

        image, filename, text_content = self.loader.get_next_image(loop == "true")

        if image is None:
            return (None, None, "", "", "0")

        mask = self.generate_mask(image, allow_RGBA_output)

        if allow_RGBA_output == "false" and image.mode != "RGB":
            image = image.convert("RGB")

        total_images_text = str(self.loader.get_total_images())

        return (pil2tensor(image), pil2tensor(mask), filename, text_content, total_images_text)

    # IS_CHANGED 和其他方法保持不变...
    @classmethod
    def IS_CHANGED(cls, path, pattern, loop, allow_RGBA_output, reset, **kwargs):
        if not path or not os.path.exists(path):
             return float("NaN")
        directory_mtime = cls.get_directory_mtime(path)
        loader_id = f"{path}|{pattern}"
        if (not hasattr(cls, 'loader') or cls.loader is None
                or cls.loader.key != loader_id
                or allow_RGBA_output != getattr(cls, 'prev_allow_RGBA_output', None)):
            return time.time()
        if directory_mtime != cls.loader.mtime:
            return time.time()
        if reset != getattr(cls, 'prev_reset', 0) or loop != getattr(cls, 'prev_loop', "true"):
            setattr(cls, 'prev_reset', reset)
            return time.time()
        if loop == "false" and not cls.loader.end_reached:
            return time.time()
        return float("NaN")

    @staticmethod
    def get_directory_mtime(path):
        try:
            return os.path.getmtime(path)
        except (OSError, TypeError):
            return 0.0

    def generate_mask(self, image, allow_RGBA_output):
        if allow_RGBA_output == "true" and image.mode == "RGBA":
            mask_np = np.array(image.split()[-1])
        else:
            mask_np = np.ones((image.height, image.width), dtype=np.uint8) * 255
        return Image.fromarray(mask_np, mode="L")


class BatchImageLoader:
    def __init__(self, directory_path, pattern, db):
        self.db = db
        self.directory_path = directory_path
        self.pattern = pattern
        self.key = f"{directory_path}|{pattern}"
        self.image_paths = []
        self.load_images(directory_path, pattern)
        
        # 3. 使用新的自然排序key
        self.image_paths.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
        
        self.index = self.db.get(self.key, 0)
        self.end_reached = False
        self.mtime = Simple_Load_Image_Batch.get_directory_mtime(directory_path)

    def load_images(self, directory_path, pattern):
        self.image_paths = []
        if not directory_path:
            return
        search_path = os.path.join(glob.escape(directory_path), pattern)
        try:
            for file_name in glob.glob(search_path, recursive=True):
                if os.path.splitext(file_name)[1].lower() in ALLOWED_EXT:
                    self.image_paths.append(os.path.abspath(file_name))
        except Exception as e:
            print(f"Error while searching for files in '{directory_path}': {e}")

    def get_next_image(self, loop=True):
        current_mtime = Simple_Load_Image_Batch.get_directory_mtime(self.directory_path)
        if current_mtime != self.mtime:
            print("Directory content has changed. Reloading and sorting file list.")
            self.load_images(self.directory_path, self.pattern)

            # 3. 使用新的自然排序key
            self.image_paths.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
            
            self.mtime = current_mtime
            self.index = 0

        # （后续的 get_next_image 逻辑保持不变）
        if not self.image_paths:
            return None, None, None

        if self.index >= len(self.image_paths):
            if loop:
                self.index = 0
            else:
                self.end_reached = True
                return None, None, None
        
        if not loop and self.end_reached:
             return None, None, None

        original_index = self.index
        while True:
            if self.index >= len(self.image_paths):
                if loop: self.index = 0
                else:
                    self.end_reached = True
                    return None, None, None

            image_path = self.image_paths[self.index]
            text_path = os.path.splitext(image_path)[0] + ".txt"
            
            try:
                image = Image.open(image_path)
                image = ImageOps.exif_transpose(image)
                filename = os.path.splitext(os.path.basename(image_path))[0]

                try:
                    with open(text_path, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                except FileNotFoundError:
                    text_content = ""

                next_index = self.index + 1
                self.index = next_index
                self.db.insert(self.key, self.index)
                return image, filename, text_content

            except Exception as e:
                print(f"Error loading image: {image_path}. Skipping. Error: {e}")
                self.index += 1
                if self.index == original_index:
                    print("All images in the directory failed to load.")
                    return None, None, None
                continue

    def get_total_images(self):
        return len(self.image_paths)

NODE_CLASS_MAPPINGS = {
    "ComfyUI-ZKZNodes.Simple_Load_Image_Batch": Simple_Load_Image_Batch
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ComfyUI-ZKZNodes.Simple_Load_Image_Batch": "批量加载图像"
}
