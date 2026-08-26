from flask import Flask

from routes.auth import auth
from routes.errands import errands


app = Flask(__name__)
app.register_blueprint(auth)
app.register_blueprint(errands)
app.register_blueprint(status)


if __name__ == "__main__":
    app.run(debug=True)
