"""Image transformation functions"""

from PIL import Image


def rescale_img(path: str, base_w: int) -> Image.Image:
    img = Image.open(path)

    wpercent = base_w / float(img.size[0])
    h = int((float(img.size[1]) * float(wpercent)))

    img = img.resize((base_w, h), Image.Resampling.LANCZOS)
    return img
