import re

# ==============================================================================
# 节点: 通用文本替换
# ==============================================================================
class UniversalTextReplacer:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_input": ("STRING", {"multiline": True, "forceInput": True, "default": ""}),
            },
            "optional": {
                "replacement_rules": ("STRING", {"default": "", "multiline": True, "placeholder": "在此输入替换规则，每行一个。\n格式：旧词->新词\n\n例如：\nred->blue\nbad text->"}),
                "use_regex": ("BOOLEAN", {"default": False, "label_on": "启用正则", "label_off": "普通匹配"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("处理后的文本",)
    FUNCTION = "process_text"
    CATEGORY = "ZKZ/Text"

    def process_text(self, text_input, replacement_rules="", use_regex=False):
        if not text_input:
            return ("",)

        result_text = text_input
        
        if not replacement_rules or not replacement_rules.strip():
            return (result_text,)

        lines = replacement_rules.strip().split('\n')
        for line in lines:
            if "->" in line:
                parts = line.split("->")
                old_str = parts[0].strip()
                new_str = parts[1].strip() if len(parts) > 1 else ""
                
                if not old_str: continue

                if use_regex:
                    try:
                        result_text = re.sub(old_str, new_str, result_text, flags=re.IGNORECASE)
                    except re.error:
                        print(f"[UniversalReplacer] Regex Error: {old_str}")
                else:
                    result_text = result_text.replace(old_str, new_str)

        return (result_text,)
