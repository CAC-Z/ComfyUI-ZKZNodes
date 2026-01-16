class ImageSwitchNode:
    CATEGORY = "ZKZ/Image"
    RETURN_TYPES = ("IMAGE","IMAGE",)
    RETURN_NAMES = ("image_1", "image_2",)

    FUNCTION = "execute"  # ADD THIS LINE: Explicitly define the execution function

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "condition": ("STRING", {"default": "0"}),
            }
        }

    OUTPUT_NODE = False

    def execute(self, image, condition):
        if condition == "1":
            return (image, None)
        else:
            return (None, image)
