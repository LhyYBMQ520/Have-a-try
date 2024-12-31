import hashlib
import logging
import os
from datetime import datetime
import platform
import yaml

from PIL import Image,ImageSequence
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, render_template, send_from_directory, abort
from waitress import serve
from concurrent.futures import ProcessPoolExecutor
from functools import partial

# 初始化Flask应用
app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

# 让日志显示日期
# 获取默认的handler
default_handler = logging.root.handlers[0]

# 创建一个新的Formatter，设置日志格式
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# 设置handler的Formatter
default_handler.setFormatter(formatter)

# 全局变量
image_data = {}  # 原始文件名与压缩文件名的映射

# 配置文件

config:dict=dict()

default_config="""
port: 5000
bind_ip: '*'
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

init_conf()

# 配置图片文件夹路径
app.config['IMAGE_FOLDER'] = config.get("image_folder","static/images")  # 输入目录
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
    with Image.open(input_path) as img_pointer:
        # 判断是否为动图
        if img_pointer.info.get('duration') is not None and config.get("preview_anime",True):
            compress_anime(img_pointer, output_path, quality)
        else:
            compress_static(img_pointer,output_path,quality)

def compress_static(img_pointer:Image.Image,output_path:str,quality:int):
    """压缩静态图片如普通图片或单帧GIF等"""
    if img_pointer.mode != 'RGB':
        img_pointer = img_pointer.convert('RGB')
    save_as_webp(img_pointer, output_path, quality)

def compress_anime(img_pointer:Image.Image, output_path:str=None, quality=20):
    max_size:tuple=(config.get("anime_max_size",200),config.get("anime_max_size",200))
    """压缩动态GIF等动画图片文件，保持所有帧并降低质量和分辨率"""
    # 获取GIF的持续时间
    duration = img_pointer.info.get('duration')

    old_frames=0
    # 保存每一帧的图像
    frames:list[Image.Image] = []
    for frame in ImageSequence.Iterator(img_pointer):
        old_frames+=1


        # 为了计算新的尺寸，先记录原始的纵横比
        original_width, original_height = frame.size
        aspect_ratio = original_width / original_height

        # 先压缩每一帧
        frame = frame.convert("RGBA")  # 转换为RGBA模式，确保支持透明背景
        frame = frame.resize(max_size, Image.Resampling.LANCZOS)  # 重新调整大小（如有需要）

        
        # 计算缩放后的宽度和高度
        if original_width > original_height:
            new_width = min(original_width, max_size[0])
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = min(original_height, max_size[1])
            new_width = int(new_height * aspect_ratio)

        
        # 重新调整大小，保持纵横比
        frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 压缩每一帧的质量，可以使用不同的压缩方法来调整图像质量
        frame = frame.convert("P", palette=Image.ADAPTIVE, colors=256)  # 降低颜色深度

        frames.append(frame)
    # 保存新的GIF文件，保留所有帧
    save_as_webp(frames[0],output_path,quality,{
        "frames":frames,
        "duration":duration
    })


def save_as_webp(img:Image.Image, output_path:str, quality=80,anime_data:dict=None):
    """保存为 WebP 格式，限制最大尺寸"""
    max_dim = 16383  # WebP 的最大尺寸限制
    if img.size[0] > max_dim or img.size[1] > max_dim:
        scale = min(max_dim / img.size[0], max_dim / img.size[1])
        img = img.resize((int(img.size[0] * scale), int(img.size[1] * scale)), Image.Resampling.LANCZOS)
    if anime_data is None:
        img.save(output_path, 'WEBP', quality=quality)
    else:
        anime_data["frames"][0].save(
            output_path, 'WEBP', quality=quality,
            save_all=True,
            loop=0,
            optimize=False,
            append_images=anime_data["frames"][1:],  # 添加剩余帧
            duration=anime_data["duration"]  # 使用获取的持续时间
        )


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

    # 创建一个进程池
    with ProcessPoolExecutor() as executor:
        # 获取所有待处理的文件路径
        files_to_compress = [
            os.path.join(app.config['IMAGE_FOLDER'], filename)
            for filename in os.listdir(app.config['IMAGE_FOLDER'])
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
        ]
        
        # 为每个文件生成对应的压缩路径
        compress_paths = [
            os.path.join(compress_folder, generate_hashed_filename(file_path))
            for file_path in files_to_compress
        ]

        # 使用 `partial` 函数避免重复传递相同参数（`compress_folder`）
        compress_func = partial(compress_image_in_process, compress_folder)

        # 提交所有的压缩任务
        list(executor.map(compress_func, files_to_compress, compress_paths))

    # 在所有图片压缩完成后调用刷新函数
    refresh_images_list()



def compress_image_in_process(compress_folder, file_path, compress_path):
    """这个函数会被多进程执行，负责压缩图片"""
    if not os.path.exists(compress_path):
        compress_image(file_path, compress_path)

def refresh_images_list():
    """ 扫描文件夹中所有图片，并依此生成目前所有可用图片的列表"""
    # 初始化 image_data
    global image_data
    image_folder = app.config['IMAGE_FOLDER']
    image_data = {
        image_name: generate_hashed_filename(os.path.join(image_folder, image_name))
        for image_name in os.listdir(image_folder)
        if image_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
    }


@app.before_request
def before_request():
    # 获取请求开始时间
    request.start_time = datetime.now()



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
    per_page = config.get("per_page",60)  # 每页显示 60 张图片

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



def log_port_used_info(portstr:str):
    if is_airplay_reciever_default_enabled_environment() is True and portstr == '5000':
        logger.error("系统中的AirPlay Reciever（监听隔空播放服务）正在占用5000端口。请将config.yml中的port项配置为其他端口后再试。")
        return
    logger.error("端口"+portstr+"被占用！请检查"+portstr+"上是否已有其他TCP协议服务，或更换其他端口")

def is_airplay_reciever_default_enabled_environment():
    # 检查占用原因是否是macOS12+上的AirPlay Reciever
    # 检测系统是否是 macOS
    if platform.system() == "Darwin":
        # 检测系统版本是否是 12.0 或以上
        version = platform.mac_ver()[0]
        major, minor, *_ = map(int, version.split("."))
        if major >= 12:
            return True
    return False




if __name__ == '__main__':
    scheduler = setup_scheduler()
    ip_address=config.get("bind_ip",['*'])
    portstr=str(config.get("port",5000))
    try:
        serve(app, listen=ip_address+':'+portstr)

    # 检查端口占用
    except OSError as e:
        log_port_used_info(portstr)
