# 简易图片库

本代码包为本项目重构前最后一个源码包，版本号：beta 0.3.0 ，后面本项目的css，html部分（尤其是css部分）将重构，以让网站页面用上新的更美观的布局，敬请期待！
即将到来的新布局参考此篇博客文章：
https://blog.csdn.net/qq_45547094/article/details/126606260

## 简介

这是一个用flask作为后端的简易网页图片库，可以将存在本地固定路径的图片展示在页面上，并提供全屏原图查看和原图的下载。

## 开始之前

启动后端前需留心有没有用pip指令安装了需要的库：
1. Flask：用于创建Web应用。
2. Pillow：用于图像处理。
3. APScheduler：用于后台任务调度。

## 如何使用

1. 下载项目源代码并解压到合适位置
2. 将需要展示的图片放在：
/static/images  文件夹中。
3. 确保设备已经正确安装并配置了Python环境
4. 打开终端，并转到源码所在位置，或直接在源码所在文件夹打开终端，输入：
```python
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
    background-image: url('/static/background/leaves.webp');      /* background/后的文件名 */
}
```

修改成实际图片的名字即可。
