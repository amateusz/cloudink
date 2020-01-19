#!/usr/bin/env python3


from PIL import Image


# Set up the inky wHAT display and border colour

def prepare(img) -> Image:
    # Get the width and height of the image

    w, h = img.size

    # Calculate the new height and width of the image

    h_new = 300
    w_new = int((float(w) / h) * h_new)
    w_cropped = 400

    # Resize the image with high-quality resampling

    img = img.resize((w_new, h_new), resample=Image.LANCZOS)

    # Calculate coordinates to crop image to 400 pixels wide

    x0 = (w_new - w_cropped) / 2
    x1 = x0 + w_cropped
    y0 = 0
    y1 = h_new

    # Crop image

    img = img.crop((x0, y0, x1, y1))

    # Convert the image to use a white / black / red colour palette

    pal_img = Image.new("P", (1, 1))
    red_pal = (255, 0, 0)
    black_pal = (0, 0, 0)
    white_pal = (255, 255, 255)
    pal_img.putpalette((255, 255, 255, 0, 0, 0, 255, 0, 0) + (0, 0, 0) * 252)
    img = img.convert("RGB").quantize(palette=pal_img)

    return img


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--image', '-i', type=str, required=True, help="Input image to be converted/displayed")
    args = parser.parse_args()

    img_file = args.image

    img_in = Image.open(img_file)
    img_out = prepare(img_in)


    def try_real_hw():
        try:
            from inky import InkyWHAT
            inky_display = InkyWHAT('red')
            inky_display.set_border(inky_display.WHITE)
            return inky_display
        except ImportError:
            return None


    real = try_real_hw()
    if real:
        real.set_image(img_out.rotate(180))
        real.show(busy_wait=True)
    else:
        # img_out.putpalette((190, 190, 190, 25, 25, 25, 150, 20, 60) + (0, 0, 0) * 252)
        img_out = img_out.resize((img_out.size[0] * 2, img_out.size[1] * 2))
        img_out.show()
        from datetime import datetime

        img_out.save(str(datetime.now().timestamp()) + '.gif')

    # Open our image file that was passed in from the command line
