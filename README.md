# 简易图片库

本代码包为本项目重构前最后一个源码包，版本号：0.3.0 ，后面本项目的css，html部分（尤其是css部分）将重构，以让网站页面用上新的更美观的布局，敬请期待！
即将到来的新布局参考此篇博客文章：
https://blog.csdn.net/qq_45547094/article/details/126606260

## 简介

这是一个用flask作为后端的简易网页图片库，可以将存在本地固定路径的图片展示在页面上，并提供全屏原图查看和原图的下载。

## 如何使用

1. 下载项目源代码并解压到合适位置
2. 确保设备已经正确安装并配置了Python环境
3. 为了防止与系统中的其他pip包发生冲突，建议为项目**创建虚拟环境**
4. 如果第一次使用本软件，请在项目根目录执行`pip install -r requirements.txt`安装必要的运行前置。使用时需要虚拟环境，请**先激活虚拟环境**再执行命令
6. 将需要展示的图片放在`static/images`文件夹中。
7. 在项目的根目录启动终端，如果你需要使用虚拟环境运行，请先激活虚拟环境。然后执行：
```sh
python3 app.py
```
即可运行后端。

（注意：第一次或后续有新增图片后开启后端时会初始化一段时间，此时Pillow正在按预设压缩图片，压缩后的图片为80%质量的webp图像，保存在：  
/static/compressed_images 文件夹中。）

5. 随后即可从 127.0.0.1 或 localhost:5000 或 公网（仅支持ipv4）访问网页。

## 其他事项

本代码包附带了一张背景图片，位于`/static/background/`中
如需自定义可以将新图片的名字改为和现在一样（leaves.webp）
也可以到`/static/css/`中修改css的这个部分：

```css
/* 设置背景图片 */
body {
    /* background/后的文件名 */
    background-image: url('/static/background/leaves.webp');
}
```

修改成实际图片的名字即可。
