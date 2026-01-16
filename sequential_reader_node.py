# 文件名: sequential_reader_node.py (最终修正版)

import os
import uuid  # 导入uuid库来生成唯一ID

class SequentialReaderNode:
    """
    一个ComfyUI节点，用于按顺序逐行读取文本文件。
    使用 IS_CHANGED 方法来确保每次队列运行时都会执行，解决了缓存问题。
    """
    _lines = []
    _current_index = 0
    _cached_filepath = None

    @classmethod
    def IS_CHANGED(cls, file_path, reset):
        """
        这个特殊方法用来告诉ComfyUI此节点的状态是否已更改。
        通过每次返回一个唯一的ID，我们强制ComfyUI在每个队列运行时都重新执行此节点。
        这是解决缓存问题的关键。
        """
        # 每次都返回一个不同的随机字符串，强制节点刷新
        return str(uuid.uuid4())

    @classmethod
    def INPUT_TYPES(cls):
        """
        定义节点的输入参数。
        """
        return {
            "required": {
                "file_path": ("STRING", {
                    "multiline": False,
                    "default": ""
                }),
                "reset": (["disable", "enable"],),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "read_sequential_line"
    CATEGORY = "ZKZ"

    def read_sequential_line(self, file_path, reset):
        """
        核心逻辑函数。
        """
        cls = self.__class__

        # 仅在文件路径更改或手动重置时才重新加载文件和重置索引
        if cls._cached_filepath != file_path or reset == "enable":
            cls._cached_filepath = file_path
            cls._current_index = 0
            cls._lines = []
            
            if not os.path.exists(file_path):
                print(f"警告 (顺序文本读取): 文件未找到于 '{file_path}'")
                return {"ui": {"string": ["文件未找到!"]}, "result": ("",)}
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    cls._lines = [line.strip() for line in f if line.strip()]
            except Exception as e:
                print(f"错误 (顺序文本读取): 读取文件时发生错误 '{file_path}': {e}")
                return {"ui": {"string": ["文件读取错误!"]}, "result": ("",)}

        if not cls._lines:
            return {"ui": {"string": ["文件为空!"]}, "result": ("",)}

        if cls._current_index >= len(cls._lines):
            cls._current_index = 0

        line_to_return = cls._lines[cls._current_index]

        # 索引递增
        cls._current_index = (cls._current_index + 1) % len(cls._lines)

        return {"ui": {"string": [line_to_return]}, "result": (line_to_return,)}


NODE_CLASS_MAPPINGS = {
    "SequentialReaderNode_ZKZ": SequentialReaderNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SequentialReaderNode_ZKZ": "顺序文本读取"
}
