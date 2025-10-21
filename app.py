from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import boto3

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'data/flood_reports.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create a model for the flood report
class FloodReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    photo = db.Column(db.String(150))  # For storing file path (optional)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Create the database
with app.app_context():
    db.create_all()

# Function to check allowed extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/report', methods=['GET', 'POST'])
def report_flood():
    if request.method == 'POST':
        location = request.form['location']
        description = request.form['description']
        photo = request.files.get('photo')

        # Save the photo if it is allowed
        photo_filename = None
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            photo_filename = filename

        # Save the report to the database
        new_report = FloodReport(location=location, description=description, photo=photo_filename)
        db.session.add(new_report)
        db.session.commit()

        # Send an SNS notification
        send_sns_alert(location, None, None, description)

        return f"Flood report submitted for {location} with description: {description}"
    return render_template('report_flood.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/reports')
def view_reports():
    reports = FloodReport.query.all()
    return render_template('view_reports.html', reports=reports)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        otp = request.form['otp']
        # Add OTP verification logic here
        if otp == "1234":  # Replace with actual verification logic
            return "Login successful!"
        else:
            return "Invalid OTP, please try again."
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return "Passwords do not match!"

        # Add logic to save user details to database
        # Example:
        # new_user = User(name=name, email=email, phone=phone, password=hash_password(password))
        # db.session.add(new_user)
        # db.session.commit()

        return "Registration successful!"
    return render_template('register.html')


# Set AWS SNS configuration
AWS_REGION = 'us-east-1'  # e.g., 'us-east-1'
AWS_ACCESS_KEY_ID = 'AKIAUPMYNIFTOW2FE35E'
AWS_SECRET_ACCESS_KEY = '2eE7lp9k9mFgRGHQe+VGn9m7gqYUtErmL5TBgLIr'
SNS_TOPIC_ARN = 'arn:aws:iam::307946668390:user/Ramu881'  # ARN of your SNS topic

sns_client = boto3.client(
    'sns',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Function to send an SNS alert
def send_sns_alert(location, latitude, longitude, description):
    try:
        message = f"New flood report at {location}.\n\nDescription: {description}"
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject='Flood Report Alert'
        )
        print(f"SNS message sent: {response}")
    except Exception as e:
        print(f"Failed to send SNS alert: {e}")

if __name__ == "__main__":
    # Ensure the upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
