from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta, timezone
from functools import wraps
import os
from werkzeug.utils import secure_filename
from app.database import get_session, init_db
from app.crud import (
    create_user, create_watering_log, verify_password, get_user_by_username, get_user_by_id,
    create_plant, get_user_plants, get_plant_by_id, delete_plant,
    update_user_password, update_user_username
)
from app.models import FrequencyEnum
from app.api import PlantApiImpl


app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 мб максимально
UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads', 'plants')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/auth', methods=['GET'])
def auth():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('auth.html')


@app.route('/auth/login', methods=['POST'])
def login():
    print(f"\n[LOGIN] Login attempt with username: {request.form.get('username')}")
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        print("[LOGIN FAILED] Username or password missing")
        return render_template('auth.html', error='Username and password are required'), 400
    
    db = get_session()
    try:
        user = verify_password(db, username, password)
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            print(f"[LOGIN SUCCESS] User {username} logged in (ID: {user.id})")
            return redirect(url_for('dashboard'))
        else:
            print(f"[LOGIN FAILED] Invalid credentials for user: {username}")
            return render_template('auth.html', error='Invalid username or password'), 401
    finally:
        db.close()


@app.route('/auth/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    print(f"\n[SIGNUP] Signup attempt with username: {username}")
    
    if not all([username, password, confirm_password]):
        print("[SIGNUP FAILED] Missing required fields")
        return render_template('auth.html', error='All fields are required'), 400
    
    if len(username) < 3 or len(username) > 50:
        print(f"[SIGNUP FAILED] Username length invalid: {len(username)} chars")
        return render_template('auth.html', error='Username must be 3-50 characters'), 400
    
    if len(password) < 6:
        print("[SIGNUP FAILED] Password too short")
        return render_template('auth.html', error='Password must be at least 6 characters'), 400
    
    if password != confirm_password:
        print("[SIGNUP FAILED] Passwords do not match")
        return render_template('auth.html', error='Passwords do not match'), 400
    
    db = get_session()
    try:
        user = create_user(db, username, password)
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            print(f"[SIGNUP SUCCESS] New user created: {username} (ID: {user.id})")
            return redirect(url_for('dashboard'))
        else:
            username = session.get('username', 'Unknown')
            print(f"[SIGNUP FAILED] Username already exists: {username}")
            return render_template('auth.html', error='Username already exists'), 400
    finally:
        db.close()


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth'))


@app.route('/')
@login_required
def dashboard():
    db = get_session()
    try:
        user_id = session.get('user_id')
        plants = get_user_plants(db, user_id)
        
        today = datetime.now().strftime('%A, %B %d, %Y')
        return render_template(
            'dashboard.html',
            today_date=today,
            plants_to_water=[],  # Placeholder - would be calculated from watering schedules
            all_plants=plants,
            username=session.get('username')
        )
    finally:
        db.close()


@app.route('/add-plant', methods=['GET', 'POST'])
@login_required
def add_plant():
    if request.method == 'POST':
        print("\n" + "="*60)
        print("PLANT FORM SUBMITTED")
        print("="*60)
        
        db = get_session()
        try:
            user_id = session.get('user_id')
            print(f"User ID: {user_id}")
            
            plant_name = request.form.get('name')

            photo_url = None
            plant_description = None
            identified_plant_name = None
            
            if 'photo' in request.files:
                file = request.files['photo']
                print(f"Photo file received: {file.filename}")
                
                if file and file.filename and allowed_file(file.filename):
                    print(f"File validation passed")
                    filename = secure_filename(f"{user_id}_{datetime.now().timestamp()}_{file.filename}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    print(f"Saving file to: {file_path}")
                    file.save(file_path)
                    photo_url = f"/static/uploads/plants/{filename}"
                    print(f"File saved successfully. Photo URL: {photo_url}")
                    
                    try:
                        print("Attempting to identify plant using API...")
                        plant_api = PlantApiImpl()
                        identified_plant_name = plant_api.identify_plant(file_path)
                        print(f"Plant identified as: {identified_plant_name}")
                        
                        plant_description = plant_api.get_plant_care_info(identified_plant_name)
                        print(f"Care info retrieved (length: {len(plant_description) if plant_description else 0} chars)")
                    except Exception as e:
                        print(f"Error identifying plant: {e}")
                        print(f"Error type: {type(e).__name__}")
                else:
                    print(f"File validation failed - File: {file}, Filename: {file.filename if file else 'None'}")
            else:
                print("No photo file in request")
            
            print(f"Creating plant in database...")
            plant = create_plant(
                db,
                user_id=user_id,
                name=plant_name,
                species=identified_plant_name,
                description=plant_description,
                photo_url=photo_url,
                watering_frequency=watering_frequency,
            )
            
            if plant:
                print(f"Plant created successfully! Plant ID: {plant.id}")
                print("="*60 + "\n")
                return redirect(url_for('dashboard'))
            else:
                print("Plant creation returned None")
                print("="*60 + "\n")
                return render_template('add_plant.html', error='Failed to create plant'), 400
        except Exception as e:
            print(f"Error creating plant: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            print("="*60 + "\n")
            return render_template('add_plant.html', error=f'An error occurred: {str(e)}'), 500
        finally:
            db.close()
    
    print("[GET /add-plant] User accessed plant creation form")
    return render_template('add_plant.html')


@app.route('/plant/<int:plant_id>')
@login_required
def plant_profile(plant_id):
    db = get_session()
    try:
        plant = get_plant_by_id(db, plant_id)
        
        if not plant or plant.user_id != session.get('user_id'):
            return redirect(url_for('dashboard'))
        
        return render_template('plant_profile.html', plant=plant)
    finally:
        db.close()


@app.route('/plant/<int:plant_id>/delete', methods=['POST'])
@login_required
def delete_plant_route(plant_id):
    print(f"\n[DELETE PLANT] Attempting to delete plant ID: {plant_id}")
    db = get_session()
    try:
        plant = get_plant_by_id(db, plant_id)
        if not plant or plant.user_id != session.get('user_id'):
            print(f"[DELETE PLANT FAILED] Unauthorized or plant not found")
            return redirect(url_for('dashboard'))
        
        print(f"[DELETE PLANT] Plant '{plant.name}' belongs to user {session.get('username')}, deleting...")
        delete_plant(db, plant_id)
        print(f"[DELETE PLANT SUCCESS] Plant {plant_id} deleted")
        return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"[DELETE PLANT ERROR] {e}")
        import traceback
        print(traceback.format_exc())
        return redirect(url_for('dashboard'))
    finally:
        db.close()


@app.route('/plant/<int:plant_id>/mark-watered', methods=['POST'])
@login_required
def mark_watered(plant_id):
    print(f"\n[MARK WATERED] Attempting to mark plant ID {plant_id} as watered")
    db = get_session()
    try:
        plant = get_plant_by_id(db, plant_id)
        if not plant or plant.user_id != session.get('user_id'):
            print(f"[MARK WATERED FAILED] Unauthorized or plant not found")
            return redirect(url_for('dashboard'))
        
        # This will require a CRUD function to log the watering
        # For now, just log the action
        print(f"[MARK WATERED] Plant '{plant.name}' marked as watered by {session.get('username')}")
        # print(f"[MARK WATERED] Watering amount: {plant.watering_amount} ml")
        
        # TODO: Call create_watering_log() CRUD function here
        log = create_watering_log(db, plant_id, datetime.now(timezone.utc))
        
        return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"[MARK WATERED ERROR] {e}")
        import traceback
        print(traceback.format_exc())
        return redirect(url_for('dashboard'))
    finally:
        db.close()


@app.route('/profile')
@login_required
def user_profile():
    db = get_session()
    try:
        user_id = session.get('user_id')
        user = get_user_by_id(db, user_id)
        return render_template('user_profile.html', user=user)
    finally:
        db.close()


@app.route('/profile/change-credentials', methods=['POST'])
@login_required
def change_credentials():
    db = get_session()
    try:
        user_id = session.get('user_id')
        current_password = request.form.get('current_password')
        new_username = request.form.get('new_username')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        user = get_user_by_id(db, user_id)
        verified = verify_password(db, user.username, current_password)
        
        if not verified:
            return render_template('user_profile.html', user=user, error='Current password is incorrect'), 401
        
        if new_username:
            if len(new_username) < 3:
                return render_template('user_profile.html', user=user, error='Username must be at least 3 characters'), 400
            user = update_user_username(db, user_id, new_username)
            if not user:
                return render_template('user_profile.html', user=user, error='Username already exists'), 400
            session['username'] = new_username
        
        # Update password if provided
        if new_password:
            if len(new_password) < 6:
                return render_template('user_profile.html', user=user, error='Password must be at least 6 characters'), 400
            if new_password != confirm_password:
                return render_template('user_profile.html', user=user, error='Passwords do not match'), 400
            update_user_password(db, user_id, new_password)
        
        return redirect(url_for('user_profile'))
    finally:
        db.close()


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
