from flask import Flask, render_template

app = Flask(__name__)

# 路由示例：主页
@app.route('/')
def home():
    return render_template('index.html')

# 路由示例：关于页面
@app.route('/about')
def about():
    return render_template('about.html')

# 启动服务器
if __name__ == '__main__':
    app.run(debug=True)
