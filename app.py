from flask import Flask, render_template, send_from_directory, request, abort
import os
from PIL import Image
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import sys
import signal
import yaml

app = Flask(__name__)

config=dict()

# 从配置文件或环境变量中读取图片文件夹路径
app.config['IMAGE_FOLDER'] = 'static/images'
app.config['COMPRESSED_FOLDER'] = 'static/compressed_images'

def compress_image(input_path, output_path, quality=80):
    with Image.open(input_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # 保存为 WebP 格式，质量为 80
        save_as_webp(img, output_path, quality)

def save_as_webp(img, output_path, quality=80):
    max_dim = 16383  # WebP的最大尺寸限制
    # 检查图片是否超过WebP的最大尺寸限制
    if img.size[0] > max_dim or img.size[1] > max_dim:
        # 计算缩放比例
        scale = min(max_dim / img.size[0], max_dim / img.size[1])
        # 缩放图片
        img = img.resize((int(img.size[0] * scale), int(img.size[1] * scale)), Image.Resampling.LANCZOS)
    # 保存为WebP格式
    img.save(output_path, 'WEBP', quality=quality)

def check_and_compress_images():
    compress_folder = app.config['COMPRESSED_FOLDER']
    if not os.path.exists(compress_folder):
        os.makedirs(compress_folder)

    # 检查压缩文件夹中的每个文件是否存在对应的原图
    for filename in os.listdir(compress_folder):
        if filename.lower().endswith(('.webp',)):
            original_filename = os.path.splitext(filename)[0]
            original_path = os.path.join(app.config['IMAGE_FOLDER'], original_filename + '.png')  # 假设原始文件是png格式
            if not os.path.exists(original_path):
                # 尝试不同的原始文件扩展名
                for ext in ['.png', '.jpg', '.jpeg', '.gif']:
                    original_path = os.path.join(app.config['IMAGE_FOLDER'], original_filename + ext)
                    if os.path.exists(original_path):
                        break
                else:  # 如果没有找到对应的原图
                    os.remove(os.path.join(compress_folder, filename))

    # 压缩新的或修改过的图片
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
    check_and_compress_images()  # Initial check at startup
    return scheduler

default_config="""
port: 5000
"""

def init_conf():
    file=None
    if list.count(os.listdir("."),"config.yml") == 0:
        file=open("config.yml",mode='w+')
        file.write(default_config)
    else:
        file=open("config.yml",mode='r')
    #将文件指针重置到开头，方便后续读取文件
    file.seek(0,0)
    global config
    config=yaml.safe_load(file.read())
    file.close()

scheduler = setup_scheduler()



# 创建一个事件标志用于通知线程退出
# exit_event = threading.Event()

def run_ipv4():
    app.run(host='0.0.0.0', port=config["port"], debug=True, threaded=True,use_reloader=False)

def run_ipv6():
    app.run(host='::', port=config["port"], debug=True, threaded=True,use_reloader=False)

"""
def signal_handler(sig, frame):
    print("\nServer Stop Requested.")
    exit_event.set()  # 设置退出标志，通知所有线程退出
    sys.exit(0)
    sys.exit(0)
"""

if __name__ == '__main__':
    init_conf()
    # 捕获 Ctrl+C (SIGINT) 信号
    run_ipv4()
