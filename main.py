from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timezone
from functools import wraps
import os
from werkzeug.utils import secure_filename
from app.database import get_session, init_db
from app.crud import (
    create_user, create_watering_log, get_water_needing_plants, verify_password, get_user_by_username, get_user_by_id,
    create_plant, get_user_plants, get_plant_by_id, delete_plant,
    update_user_password, update_user_username
)
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
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return render_template('auth.html', error='Username and password are required'), 400
    
    db = get_session()
    try:
        user = verify_password(db, username, password)
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            return render_template('auth.html', error='Invalid username or password'), 401
    finally:
        db.close()


@app.route('/auth/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([username, password, confirm_password]):
        return render_template('auth.html', error='All fields are required'), 400
    
    if len(username) < 3 or len(username) > 50:
        return render_template('auth.html', error='Username must be 3-50 characters'), 400
    
    if len(password) < 6:
        return render_template('auth.html', error='Password must be at least 6 characters'), 400
    
    if password != confirm_password:
        return render_template('auth.html', error='Passwords do not match'), 400
    
    db = get_session()
    try:
        user = create_user(db, username, password)
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
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
        plants_to_water = get_water_needing_plants(db, user_id)
        
        today = datetime.now().strftime('%A, %B %d, %Y')
        return render_template(
            'dashboard.html',
            today_date=today,
            plants_to_water=plants_to_water,
            all_plants=plants,
            username=session.get('username')
        )
    finally:
        db.close()


@app.route('/add-plant', methods=['GET', 'POST'])
@login_required
def add_plant():
    if request.method == 'POST':
        db = get_session()
        try:
            user_id = session.get('user_id')
            
            plant_name = request.form.get('name')

            photo_url = None
            plant_description = None
            identified_plant_name = None
            
            if 'photo' in request.files:
                file = request.files['photo']
                
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{user_id}_{datetime.now().timestamp()}_{file.filename}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    file.save(file_path)
                    photo_url = f"/static/uploads/plants/{filename}"
                    
                    try:
                        plant_api = PlantApiImpl()
                        plant_data = plant_api.identify_plant(file_path)
                        identified_plant_name = plant_data[0]
                        plant_description = plant_data[1]
                        watering_frequency = plant_data[2]
                    except Exception as e:
                        pass
            
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
                return redirect(url_for('dashboard'))
            else:
                return render_template('add_plant.html', error='Failed to create plant'), 400
        except Exception as e:
            return render_template('add_plant.html', error=f'An error occurred: {str(e)}'), 500
        finally:
            db.close()
    
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
    db = get_session()
    try:
        plant = get_plant_by_id(db, plant_id)
        if not plant or plant.user_id != session.get('user_id'):
            return redirect(url_for('dashboard'))
        
        delete_plant(db, plant_id)
        return redirect(url_for('dashboard'))
    except Exception as e:
        return redirect(url_for('dashboard'))
    finally:
        db.close()


@app.route('/plant/<int:plant_id>/mark-watered', methods=['POST'])
@login_required
def mark_watered(plant_id):
    db = get_session()
    try:
        plant = get_plant_by_id(db, plant_id)
        if not plant or plant.user_id != session.get('user_id'):
            return redirect(url_for('dashboard'))
        
        log = create_watering_log(db, plant_id, datetime.now(timezone.utc))
        return redirect(url_for('dashboard'))
    except Exception as e:
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
    app.run(debug=False, host='0.0.0.0', port=5000)
