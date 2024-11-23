import hashlib
import logging
import os
from datetime import datetime

from PIL import Image
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, render_template, send_from_directory, abort
from waitress import serve

# 初始化Flask应用
app = Flask(__name__)

# 配置日志
# 设置根日志记录器
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)
# 设置访问日志记录器
access_logger = logging.getLogger('access')
access_logger.setLevel(logging.INFO)
# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
# 创建访问日志格式化器
access_formatter = logging.Formatter(
    '%(asctime)s - %(client_ip)s - %(request_method)s %(request_url)s - %(status_code)s - Time Taken: %(elapsed_time)s')
console_handler.setFormatter(access_formatter)
# 添加访问日志处理器
access_logger.addHandler(console_handler)

# 配置图片文件夹路径
app.config['IMAGE_FOLDER'] = 'static/images'  # 输入目录
app.config['COMPRESSED_FOLDER'] = 'static/compressed_images'  # Webp输出目录

def generate_hashed_filename(original_path):
    """基于文件内容生成哈希值文件名"""
    with open(original_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()[:4]  # MD5 哈希值前四位
    base_name = os.path.splitext(os.path.basename(original_path))[0]
    return f"{base_name}_{file_hash}.webp"

def compress_image(input_path, output_path=None, quality=80):
    """压缩图片并保存为指定路径"""
    if output_path is None:  # 如果没有指定输出路径，自动生成
        output_path = os.path.join(
            app.config['COMPRESSED_FOLDER'],
            generate_hashed_filename(input_path)
        )
    with Image.open(input_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        save_as_webp(img, output_path, quality)

def save_as_webp(img, output_path, quality=80):
    """保存为 WebP 格式，限制最大尺寸"""
    max_dim = 16383  # WebP 的最大尺寸限制
    if img.size[0] > max_dim or img.size[1] > max_dim:
        scale = min(max_dim / img.size[0], max_dim / img.size[1])
        img = img.resize((int(img.size[0] * scale), int(img.size[1] * scale)), Image.Resampling.LANCZOS)
    img.save(output_path, 'WEBP', quality=quality)

def check_and_compress_images():
    """检查和压缩图片"""
    compress_folder = app.config['COMPRESSED_FOLDER']
    if not os.path.exists(compress_folder):
        os.makedirs(compress_folder)

    # 删除多余的压缩文件
    for filename in os.listdir(compress_folder):
        if filename.lower().endswith('.webp'):
            # 原始文件路径
            original_filename = '_'.join(filename.split('_')[:-1])  # 去掉哈希部分
            original_path = os.path.join(app.config['IMAGE_FOLDER'], original_filename + '.png')
            if not os.path.exists(original_path):
                for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                    original_path = os.path.join(app.config['IMAGE_FOLDER'], original_filename + ext)
                    if os.path.exists(original_path):
                        break
                else:
                    os.remove(os.path.join(compress_folder, filename))

    # 压缩新文件
    for filename in os.listdir(app.config['IMAGE_FOLDER']):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            file_path = os.path.join(app.config['IMAGE_FOLDER'], filename)
            hashed_filename = generate_hashed_filename(file_path)
            compress_path = os.path.join(compress_folder, hashed_filename)
            if not os.path.exists(compress_path):
                compress_image(file_path, compress_path)

@app.before_request
def log_request_info():
    """记录访问日志"""
    request.start_time = datetime.now()
    request.client_ip = request.remote_addr
    request.request_method = request.method
    request.request_url = request.url

@app.after_request
def log_response_info(response):
    """记录响应日志"""
    elapsed_time = datetime.now() - request.start_time
    log_message = (
        f"IP: {request.client_ip} | Method: {request.method} | URL: {request.url} "
        f"| Status Code: {response.status_code} | Time Taken: {elapsed_time.total_seconds():.4f}s"
    )
    # 使用 extra 参数传递信息
    logger.info(log_message, extra={
        'client_ip': request.client_ip,
        'request_method': request.method,
        'request_url': request.url,
        'status_code': response.status_code,
        'elapsed_time': elapsed_time.total_seconds()
    })
    return response

@app.route('/')
def index():
    """主页，显示图片列表"""
    image_folder = app.config['IMAGE_FOLDER']
    image_names = [f for f in os.listdir(image_folder) if
                   f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    page = int(request.args.get('page', 1))
    per_page = 60  # 每页显示 60 张图片
    total_pages = (len(image_names) + per_page - 1) // per_page
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    images_on_page = image_names[start_index:end_index]
    return render_template('index.html', image_names=images_on_page, page=page, total_pages=total_pages)

@app.route('/image/<filename>')
def serve_image(filename):
    """返回压缩的图片文件"""
    compress_folder = app.config['COMPRESSED_FOLDER']
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        abort(400, description="Invalid image file extension.")
    # 查找哈希文件名
    original_name = os.path.splitext(filename)[0]
    for file in os.listdir(compress_folder):
        if file.startswith(original_name) and file.endswith('.webp'):
            return send_from_directory(compress_folder, file)
    # 找不到压缩文件时，返回原始文件
    return send_from_directory(app.config['IMAGE_FOLDER'], filename)

@app.route('/original/<filename>')
def serve_original(filename):
    """返回原始的图片文件"""
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        abort(400, description="Invalid image file extension.")
    return send_from_directory(app.config['IMAGE_FOLDER'], filename)

def setup_scheduler():
    """设置定时任务"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_compress_images, 'interval', hours=1)
    scheduler.start()
    check_and_compress_images()  # 应用启动时立即执行一次图片压缩检查
    return scheduler

scheduler = setup_scheduler()

if __name__ == '__main__':
    serve(app, listen='*:5000')