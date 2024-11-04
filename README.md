本代码包为本项目重构前最后一个源码包，版本号：beta 0.3.0 ，后面本项目的css，html部分（尤其是css）将重构，以让网站页面换上新的更好看的布局，敬请期待！

本代码包附带了一张背景图片，位于`/static/background/`中
如需自定义可以将新图片的名字改为和现在一样
也可以到`/static/css/`中修改css的这个部分：

```css
/* 设置背景图片 */
body {
    background-image: url('/static/background/leaves.webp');      /* background/后的文件名 */
}
```
修改成实际图片的名字即可。

网页上要展示的图片放在  /static/images/  中。
启动后端前需留心有没有pip安装了需要的库：
1. Flask：用于创建Web应用。
2. Pillow（PIL的更新分支）：用于图像处理。
3. APScheduler：用于后台任务调度。

第一次开启会初始化一段时间，此时Pillow正在按预设压缩图片，保存在：  
/static/compressed_images/  中。

随后即可从  127.0.0.1/localhost:5000  ，公网（单ipv4）访问。
