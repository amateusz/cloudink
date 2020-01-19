import os
from pathlib import Path

from PIL import Image
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

import prepare_colourspace
from prepare_brightness import threshold, get_modified, percv_brightness

cwd_root = Path(__file__).parent.absolute()
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('uploader.html')


@app.route('/set_image', methods=['POST'])
def set_image():
    if request.form['submit_button'] == 'clicked':
        rel_src = request.form['img_rel_path']

        from shutil import copyfile
        src = cwd_root / rel_src
        new_filename = Path('bg_uploaded' + src.suffix)
        dst = cwd_root / new_filename

        from glob import glob
        to_deletes = glob(str(dst.parent / new_filename.stem) + '.*')
        for to_delete in to_deletes:
            if os.path.exists(to_delete):
                Path(to_delete).unlink()

        copyfile(src, dst)  # save it in root

    return redirect(url_for('index'))


@app.route('/upload', methods=['POST'])
def upload():
    abs_path = None
    success = False
    error = None
    try:
        file_obj = request.files['file']
        mime = file_obj.mimetype
        type, subtype = mime.split('/')
        if type != 'image':
            error = f"Wgraj obrazek, a nie jakiś szajs ({subtype} ???)"
            raise
        original_filename = secure_filename(file_obj.filename)
        from datetime import datetime
        filename_part = int(datetime.now().timestamp())
        filename = Path(str(filename_part) + Path(original_filename).suffix)
        abs_path = cwd_root / Path('static') / Path('uploads')
        file_obj.save(str(abs_path / filename))
        success = True
    except:
        raise
    finally:
        # return render_template('uploaded.html', success=success, image_path=abs_path, error=error)
        prepared = prepare_image(abs_path / filename)
        filename_prepared = Path(str(filename_part) + '.png')
        prepared.save(abs_path / 'prepared' / filename_prepared, 'PNG')
        # return send_file(prepared, mimetype=mime)
        return render_template('uploaded.html',
                               rel_img_path=str(Path('static') / Path('uploads') / 'prepared' / filename_prepared),
                               rel_return_img_path=str(Path('static') / Path('uploads') / filename))


def save_prepared(prepared_im):
    filename = 'bg_prepared.png'
    prepared_im.save(cwd_root / filename, 'PNG')


def prepare_image(im_filename):
    # oh, there is a image.
    # threshold it and then:
    # - if it is dark, then make it even darker
    # - if it is bright, make it brighter
    bg = Image.open(im_filename)

    print(f'input brightness: {percv_brightness(bg)}')
    if_brighter = threshold(bg)
    bg_1_stage = get_modified(bg, if_brighter)

    # transform to eink colourspace

    bg_2_stage = prepare_colourspace.prepare(bg_1_stage)

    # bg_2_stage.putpalette((190, 190, 190, 25, 25, 25, 150, 20, 60) + (0, 0, 0) * 252)

    # img_io = BytesIO()
    # bg_2_stage.save(img_io, 'PNG', quality=70)
    # img_io.seek(0)
    # return img_io
    return bg_2_stage


if __name__ == '__main__':
    app.run(host='0.0.0.0')
