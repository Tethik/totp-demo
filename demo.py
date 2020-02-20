import io
import json
from xml.etree import ElementTree
from flask import Flask, request, render_template
import pyotp
import base64
import pyotp.totp
import qrcode
import qrcode.image.svg


app = Flask(__name__)


class Database(object):
    db_file = 'users.json'
    users = None

    def __init__(self):
        pass

    def load(self) -> dict:
        if self.users:
            return
        try:
            with open(self.db_file) as f:
                self.users = json.load(f)
        except FileNotFoundError:
            self.users = {}

    def put(self, user: str, secret: str):
        self.load()
        self.users[user] = {"secret": secret}
        with open(self.db_file, "w+") as f:
            json.dump(self.users, f)

    def get(self, user: str):
        self.load()
        return self.users.get(user, None)


db = Database()


@app.route('/enroll', methods=['POST', 'GET'])
def enroll():
    if not request.method == 'POST':
        return render_template('enroll.html')

    secret = pyotp.random_base32()
    name = request.form.get("name")
    db.put(name, secret)
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name, issuer_name=request.form.get("issuer"))
    img = qrcode.make(uri)
    print(img)
    f = io.BytesIO()
    img.save(f, format="png")
    f.seek(0)
    b64 = base64.b64encode(f.read()).decode()
    return render_template('show.html', qr=b64)


@app.route('/verify', methods=['POST', 'GET'])
def verify():
    if not request.method == 'POST':
        return render_template('verify.html')

    name = request.form.get("name")
    code = request.form.get("code")

    user = db.get(name)
    if not user:
        return render_template('verify.html', message="No such user")

    totp = pyotp.totp.TOTP(user["secret"])

    if totp.verify(code):
        msg = f"Successful authentication for {name}"
    else:
        msg = f"Wrong code for {name}"

    return render_template('verify.html', message=msg)


@app.route('/')
def index():
    return render_template('index.html')
