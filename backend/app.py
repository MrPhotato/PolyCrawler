from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)  # 允许所有来源的跨域请求，生产环境中应配置更严格的规则

    # 导入并注册蓝图
    from backend.search.routes import search_bp
    app.register_blueprint(search_bp, url_prefix='/api') # 所有搜索相关的API都在 /api/ 下

    @app.route('/health')
    def health():
        return "Backend is healthy!"

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000) # 注意：debug=True 不应在生产环境中使用 