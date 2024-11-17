from flask import Flask, render_template, send_from_directory, request, abort
import os
from PIL import Image
from apscheduler.schedulers.background import BackgroundScheduler
from waitress import serve
import logging

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

# 从配置文件或环境变量中读取图片文件夹路径
app.config['IMAGE_FOLDER'] = 'static/images'
app.config['COMPRESSED_FOLDER'] = 'static/compressed_images'

def compress_image(input_path, output_path, quality=80):
    with Image.open(input_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        save_as_webp(img, output_path, quality)

def save_as_webp(img, output_path, quality=80):
    max_dim = 16383  # WebP的最大尺寸限制
    if img.size[0] > max_dim or img.size[1] > max_dim:
        scale = min(max_dim / img.size[0], max_dim / img.size[1])
        img = img.resize((int(img.size[0] * scale), int(img.size[1] * scale)), Image.Resampling.LANCZOS)
    img.save(output_path, 'WEBP', quality=quality)

def check_and_compress_images():
    compress_folder = app.config['COMPRESSED_FOLDER']
    if not os.path.exists(compress_folder):
        os.makedirs(compress_folder)

    for filename in os.listdir(compress_folder):
        if filename.lower().endswith(('.webp',)):
            original_filename = os.path.splitext(filename)[0]
            original_path = os.path.join(app.config['IMAGE_FOLDER'], original_filename + '.png')
            if not os.path.exists(original_path):
                for ext in ['.png', '.jpg', '.jpeg', '.gif']:
                    original_path = os.path.join(app.config['IMAGE_FOLDER'], original_filename + ext)
                    if os.path.exists(original_path):
                        break
                else:
                    os.remove(os.path.join(compress_folder, filename))

    for filename in os.listdir(app.config['IMAGE_FOLDER']):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            file_path = os.path.join(app.config['IMAGE_FOLDER'], filename)
            compress_path = os.path.join(compress_folder, os.path.splitext(filename)[0] + '.webp')
            if not os.path.exists(compress_path):
                compress_image(file_path, compress_path)

@app.route('/')
def index():
    image_folder = app.config['IMAGE_FOLDER']
    image_names = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    
    page = int(request.args.get('page', 1))
    per_page = 60  # 每页显示60张图片
    
    total_pages = (len(image_names) + per_page - 1) // per_page
    
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    images_on_page = image_names[start_index:end_index]
    
    return render_template('index.html', image_names=images_on_page, page=page, total_pages=total_pages)

@app.route('/image/<filename>')
def serve_image(filename):
    compress_folder = app.config['COMPRESSED_FOLDER']
    compress_path = os.path.join(compress_folder, os.path.splitext(filename)[0] + '.webp')
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        abort(400, description="Invalid image file extension.")
    if os.path.exists(compress_path):
        return send_from_directory(compress_folder, os.path.splitext(filename)[0] + '.webp')
    else:
        return send_from_directory(app.config['IMAGE_FOLDER'], filename)

@app.route('/original/<filename>')
def serve_original(filename):
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        abort(400, description="Invalid image file extension.")
    return send_from_directory(app.config['IMAGE_FOLDER'], filename)

def setup_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_compress_images, 'interval', hours=1)
    scheduler.start()
    check_and_compress_images()  # 应用启动时立即执行一次图片压缩检查
    return scheduler

scheduler = setup_scheduler()

if __name__ == '__main__':
    serve(app, listen='*:5000')