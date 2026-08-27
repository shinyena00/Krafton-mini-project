import os

from dotenv import load_dotenv
from flask import Flask

from routes.auth import auth
from routes.errands import errands
from routes.status import status


load_dotenv()

app = Flask(__name__)
app.register_blueprint(auth)
app.register_blueprint(errands)
app.register_blueprint(status)


if __name__ == "__main__":
    # 배포 서버에서는 디버거가 켜지지 않도록 기본값을 끔으로 둔다.
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    app.run(host="0.0.0.0", port=5000, debug=debug)
