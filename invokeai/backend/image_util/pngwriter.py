"""
Two helper classes for dealing with PNG images and their path names.
PngWriter -- Converts Images generated by T2I into PNGs, finds
             appropriate names for them, and writes prompt metadata
             into the PNG.

Exports function retrieve_metadata(path)
"""

import json
import os
import re

from PIL import Image, PngImagePlugin

# -------------------image generation utils-----


class PngWriter:
    def __init__(self, outdir):
        self.outdir = outdir
        os.makedirs(outdir, exist_ok=True)

    # gives the next unique prefix in outdir
    def unique_prefix(self):
        # sort reverse alphabetically until we find max+1
        dirlist = sorted(os.listdir(self.outdir), reverse=True)
        # find the first filename that matches our pattern or return 000000.0.png
        existing_name = next(
            (f for f in dirlist if re.match(r"^(\d+)\..*\.png", f)),
            "0000000.0.png",
        )
        basecount = int(existing_name.split(".", 1)[0]) + 1
        return f"{basecount:06}"

    # saves image named _image_ to outdir/name, writing metadata from prompt
    # returns full path of output
    def save_image_and_prompt_to_png(self, image, dream_prompt, name, metadata=None, compress_level=6):
        path = os.path.join(self.outdir, name)
        info = PngImagePlugin.PngInfo()
        info.add_text("Dream", dream_prompt)
        if metadata:
            info.add_text("sd-metadata", json.dumps(metadata))
        image.save(path, "PNG", pnginfo=info, compress_level=compress_level)
        return path

    def retrieve_metadata(self, img_basename):
        """
        Given a PNG filename stored in outdir, returns the "sd-metadata"
        metadata stored there, as a dict
        """
        path = os.path.join(self.outdir, img_basename)
        all_metadata = retrieve_metadata(path)
        return all_metadata["sd-metadata"]


def retrieve_metadata(img_path):
    """
    Given a path to a PNG image, returns the "sd-metadata"
    metadata stored there, as a dict
    """
    im = Image.open(img_path)
    if hasattr(im, "text"):
        md = im.text.get("sd-metadata", "{}")
        dream_prompt = im.text.get("Dream", "")
    else:
        # When trying to retrieve metadata from images without a 'text' payload, such as JPG images.
        md = "{}"
        dream_prompt = ""
    return {"sd-metadata": json.loads(md), "Dream": dream_prompt}


def write_metadata(img_path: str, meta: dict):
    im = Image.open(img_path)
    info = PngImagePlugin.PngInfo()
    info.add_text("sd-metadata", json.dumps(meta))
    im.save(img_path, "PNG", pnginfo=info)


class PromptFormatter:
    def __init__(self, t2i, opt):
        self.t2i = t2i
        self.opt = opt

    # note: the t2i object should provide all these values.
    # there should be no need to or against opt values
    def normalize_prompt(self):
        """Normalize the prompt and switches"""
        t2i = self.t2i
        opt = self.opt

        switches = []
        switches.append(f'"{opt.prompt}"')
        switches.append(f"-s{opt.steps or t2i.steps}")
        switches.append(f"-W{opt.width or t2i.width}")
        switches.append(f"-H{opt.height or t2i.height}")
        switches.append(f"-C{opt.cfg_scale or t2i.cfg_scale}")
        switches.append(f"-A{opt.sampler_name or t2i.sampler_name}")
        # to do: put model name into the t2i object
        #        switches.append(f'--model{t2i.model_name}')
        if opt.seamless or t2i.seamless:
            switches.append("--seamless")
        if opt.init_img:
            switches.append(f"-I{opt.init_img}")
        if opt.fit:
            switches.append("--fit")
        if opt.strength and opt.init_img is not None:
            switches.append(f"-f{opt.strength or t2i.strength}")
        if opt.gfpgan_strength:
            switches.append(f"-G{opt.gfpgan_strength}")
        if opt.upscale:
            switches.append(f"-U {' '.join([str(u) for u in opt.upscale])}")
        if opt.variation_amount > 0:
            switches.append(f"-v{opt.variation_amount}")
        if opt.with_variations:
            formatted_variations = ",".join(f"{seed}:{weight}" for seed, weight in opt.with_variations)
            switches.append(f"-V{formatted_variations}")
        return " ".join(switches)
