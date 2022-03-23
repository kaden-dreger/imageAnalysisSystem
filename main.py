from datetime import datetime
from enums.cameraEnums import CameraMode, CameraStatus
from enums.eventEnums import EventType
from models.models import Users, Event, Camera
from flask import Flask, Blueprint, redirect, url_for, render_template, request, jsonify, flash
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from Forms import LoginForm, SignUpForm
from os import environ
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import boto3

bp = Blueprint('myapp', __name__)

loginManager = LoginManager()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'imageanalysissystem'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:' + environ["DB_PASSWORD"] + '@lfiasdb.cwtorsyu3gx6.us-west-2.rds.amazonaws.com/postgres'

    Bootstrap(app)

    loginManager.init_app(app)
    loginManager.login_view = 'myapp.login'

    app.register_blueprint(bp)

    from models.models import db
    db.init_app(app)

    return app
    
# EXAMPLE OF API ENDPOINT TIED TO SIMPLE-CLIENT
@bp.route("/pi", methods=["GET", "POST"])
def index():
    notdata = 'test'
    if(request.method == "POST"):
        data = 'hello_world'
        return jsonify({'data': data})
    return redirect(url_for('myapp.cameras'))
# --------

@loginManager.user_loader
def loadUser(id):
    return Users.query.get(int(id))

@bp.route("/test", methods=["GET", "POST"])
def test():
    getData = 'get_request'
    postData = 'post_request'
    if(request.method == "POST"):
        return jsonify({'data': postData})
    elif (request.method == "GET"):
        return jsonify({'data': getData})

@bp.route("/addEvent")
@login_required
def testAddEvent():
    
    newEvent = Event(user_id=current_user.id, camera_id=1, type=EventType.IMAGE_CAPTURE_SUCCESS, timestamp=datetime.now())

    newEvent.create()

    return redirect(url_for('myapp.home'))

@bp.route("/addCamera")
@login_required
def testAddCamera():
    newCamera = Camera(user_id=current_user.id, name="Camera #" + str(current_user.id), status=CameraStatus.OFFLINE, mode=CameraMode.FACIAL_RECOGNITION)
    newCamera.create()

    return redirect(url_for('myapp.home'))

@bp.route("/home")
@bp.route("/")
@login_required
def home():
    events = Event.query.order_by(Event.timestamp).limit(3).all()
    for event in events:
        event.type = event.type.value
    return render_template("home.html", name=current_user.name, events=events)

@bp.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('myapp.home'))
        flash("Invalid email/password")
    return render_template("login.html", form=form)

@bp.route("/signup", methods=['GET', 'POST'])
def signup():
    form = SignUpForm()

    if form.validate_on_submit():
        hashedPassword = generate_password_hash(form.password.data, method='sha256')

        isUserExisting = Users.query.filter_by(email=form.email.data).first()

        if not isUserExisting:
            newUser = Users(name=form.name.data, email= form.email.data, password=hashedPassword)

            newUser.create()

            return redirect(url_for('myapp.login'))
            
        flash("A user already exists with that email!")
    return render_template("signup.html", form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('myapp.login'))

@bp.route("/events")
@login_required
def events():
    events = Event.query.order_by(Event.timestamp).all()
    for event in events:
        event.type = event.type.value
    return render_template("events.html", events=events)

@bp.route("/cameras")
@login_required
def cameras():
    cameras = Camera.query.order_by(Camera.status).all()
    for camera in cameras:
        camera.status = camera.status.value
        camera.mode = camera.mode.value
    return render_template("cameras.html", cameras=cameras)

@bp.route("/train")
@login_required
def train():
    return render_template("train.html")

@bp.route("/train", methods=['POST'])
def upload_file():
    file = request.files['file']
    if file.filename != '':
        if file:
            file.filename = secure_filename(file.filename)
            output = send_to_s3(file, "lfiasimagestore")
            return str(output)
    else:
        return redirect("myapp.home")
    return redirect(url_for('myapp.train'))

def send_to_s3(file, bucket_name):
        session = boto3.Session(profile_name='default')
        s3 = session.client('s3')
        try:
            s3.upload_fileobj(
                file,
                bucket_name,
                file.filename,
                ExtraArgs={
                    "ContentType": file.content_type    #Set appropriate content type as per the file
                }
            )
        except Exception as e:
            print("Something Happened: ", e)
            return e
        return "{} recieved {}".format("us-west-2", file.filename)

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
