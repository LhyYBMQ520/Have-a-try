import hashlib
import logging
import os
from datetime import datetime
import platform
import yaml

from PIL import Image
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, render_template, send_from_directory, abort
from waitress import serve

# 初始化Flask应用
app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

# 配置图片文件夹路径
app.config['IMAGE_FOLDER'] = 'static/images'  # 输入目录
app.config['COMPRESSED_FOLDER'] = 'static/compressed_images'  # Webp输出目录

# 全局变量
image_data = {}  # 原始文件名与压缩文件名的映射


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
def before_request():
    # 获取请求开始时间
    request.start_time = datetime.now()
    # 初始化 image_data
    global image_data
    image_folder = app.config['IMAGE_FOLDER']
    image_data = {
        image_name: generate_hashed_filename(os.path.join(image_folder, image_name))
        for image_name in os.listdir(image_folder)
        if image_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
    }


@app.after_request
def log_response_info(response):
    """记录响应日志"""
    elapsed_time = datetime.now() - request.start_time
    log_message = (
        f"IP: {request.remote_addr} | Method: {request.method} | URL: {request.url} "
        f"| Status Code: {response.status_code} | Time Taken: {elapsed_time.total_seconds():.4f}s"
    )
    # 使用 extra 参数传递信息
    logger.info(log_message, extra={
        'client_ip': request.remote_addr,
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
    if filename not in image_data:
        abort(404, description="Image not found.")
    # 获取压缩文件名
    compressed_filename = image_data[filename]
    compress_folder = app.config['COMPRESSED_FOLDER']
    if not os.path.exists(os.path.join(compress_folder, compressed_filename)):
        abort(404, description="Compressed image not found.")

    return send_from_directory(compress_folder, compressed_filename)


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

default_config="""
port: 5000
bind_ips: 
  - '*'
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

if __name__ == '__main__':
    init_conf()
    for ip_address in config.get("bind_ips",['*']):
        portstr=str(config.get("port",5000))
        try:
            serve(app, listen=ip_address+':'+portstr)
            
        # 检查端口占用
        except OSError as e:
            logger.error("端口"+portstr+"被占用！请检查"+portstr+"上是否已有其他TCP协议服务，或更换其他端口")
            # 检查占用原因是否是macOS12+上的AirPlay Reciever
            # 检测系统是否是 macOS
            if platform.system() == "Darwin":
                # 检测系统版本是否是 12.0 或以上
                version = platform.mac_ver()[0]
                major, minor, *_ = map(int, version.split("."))
                if major >= 12:
                    logger.error("系统中的AirPlay Reciever（监听隔空播放服务）正在占用5000端口。请将config.yml中的port项配置为其他端口后再试。")