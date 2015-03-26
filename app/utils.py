import os
import PIL
from PIL import Image
from app import app

def generate_thumbnail(filename, filename_path, width, type):
    basewidth = width
    img = Image.open(filename_path)
    wpercent = (basewidth/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    thumbnail_img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
    thumbnail_name = type + "_" + filename
    thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_name)
    thumbnail_img.save(thumbnail_path)
    return thumbnail_name