#!/usr/bin/env python3

import math

from PIL import Image, ImageStat, ImageEnhance

target_brighter = 180
target_darker = 15.5


def avg_brightness(im):
    im = im.convert('L')
    stat = ImageStat.Stat(im)
    return stat.rms[0]


def percv_brightness(im):
    stat = ImageStat.Stat(im)
    # try:
    r, g, b = stat.mean
    # except ValueError:
    #     return avg_brightness(im)
    return math.sqrt(0.241 * (r ** 2) + 0.691 * (g ** 2) + 0.068 * (b ** 2))


def threshold(im):
    make_bright = True if percv_brightness(im) > 74 else False
    return make_bright


def make_brighter(im):
    return get_modified(im, True)


def make_darker(im):
    return get_modified(im, False)


def get_modified(im, make_brighter):
    bg_enhancer = ImageEnhance.Brightness(im)

    new_brightness = percv_brightness(im)
    if make_brighter:
        factor = 1.0
        while new_brightness <= target_brighter:
            bg_enhanced = bg_enhancer.enhance(factor)
            new_brightness = percv_brightness(bg_enhanced)
            # print(f'factor: {factor}, curr: {new_brightness}')
            factor = factor * 1.05
    else:
        factor = 1.0
        while new_brightness >= target_darker:
            bg_enhanced = bg_enhancer.enhance(factor)
            new_brightness = percv_brightness(bg_enhanced)
            # print(f'factor: {factor}, curr: {new_brightness}')
            factor = factor / 1.05

    print(f'acheived brighness: {new_brightness}')

    return bg_enhanced


if __name__ == '__main__':
    import argparse
    from prepare_colourspace import prepare

    parser = argparse.ArgumentParser()
    parser.add_argument('--image', '-i', type=str, required=True, help="Input image to be converted/displayed")
    args = parser.parse_args()

    bg = Image.open(args.image)

    input_brightness = percv_brightness(bg)
    make_bright = threshold(bg)
    print(f'input brightness: {input_brightness}. let\'s go {"brighter" if make_bright else "darker"}')

    bg_enhanced = get_modified(bg, make_bright)

    bg_prepared = prepare(bg_enhanced)
    bg_prepared.show()
