from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta


app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = 'your-secret-key-change-this'


mock_plants = [
    {
        'id': 1,
        'name': 'Monstera Deliciosa',
        'species': 'Monstera Deliciosa',
        'location': 'Living Room',
        'watering_frequency': 'Weekly',
        'watering_time': '09:00',
        'watering_amount': 500,
        'photo_url': '',
        'description': 'A beautiful climbing plant with large leaves. It features distinctive perforated leaves that develop as the plant matures. Monstera is a popular choice for indoor spaces due to its low maintenance requirements and stunning appearance.',
        'soil_type': 'Potting Mix',
        'sunlight_requirement': 'Partial Sun'
    },
    {
        'id': 2,
        'name': 'Snake Plant',
        'species': 'Sansevieria trifasciata',
        'location': 'Bedroom',
        'watering_frequency': 'Every 2 weeks',
        'watering_time': '10:00',
        'watering_amount': 250,
        'photo_url': '',
        'description': 'A low maintenance succulent with striking vertical leaves. The Snake Plant is extremely hardy and can tolerate a wide range of light conditions. It is also known for its air-purifying properties.',
        'soil_type': 'Succulent Mix',
        'sunlight_requirement': 'Partial Shade'
    },
    {
        'id': 3,
        'name': 'Pothos',
        'species': 'Epipremnum aureum',
        'location': 'Kitchen',
        'watering_frequency': 'Weekly',
        'watering_time': '08:00',
        'watering_amount': 300,
        'photo_url': '',
        'description': 'A trailing plant that is easy to care for and highly adaptable. Pothos grows quickly and can be trained to climb or cascade. It features heart-shaped leaves and is perfect for hanging baskets or shelves.',
        'soil_type': 'Potting Mix',
        'sunlight_requirement': 'Partial Shade'
    },
]

mock_user = {
    'id': 1,
    'username': 'plantlover',
    'email': 'plantlover@example.com',
    'created_at': 'January 15, 2025',
}

mock_today_watering = [
    {
        'id': 1,
        'name': 'Monstera Deliciosa',
        'species': 'Monstera Deliciosa',
        'watering_count': 1,
        'next_watering_time': '09:00 AM',
        'watering_amount': 500
    },
    {
        'id': 3,
        'name': 'Pothos',
        'species': 'Epipremnum aureum',
        'watering_count': 1,
        'next_watering_time': '10:00 AM',
        'watering_amount': 300
    },
]


@app.route('/')
def dashboard():
    today = datetime.now().strftime('%A, %B %d, %Y')
    return render_template(
        'dashboard.html',
        today_date=today,
        plants_to_water=mock_today_watering,
        all_plants=mock_plants
    )


@app.route('/add-plant', methods=['GET', 'POST'])
def add_plant():
    if request.method == 'POST':
        # Process form data here
        # For now, just redirect to dashboard
        return redirect(url_for('dashboard'))
    return render_template('add_plant.html')


@app.route('/plant/<int:plant_id>')
def plant_profile(plant_id):
    """Plant profile page showing detailed plant information."""
    # Find the plant by ID
    plant = next((p for p in mock_plants if p['id'] == plant_id), None)
    
    if not plant:
        return redirect(url_for('dashboard'))
    
    return render_template('plant_profile.html', plant=plant)


@app.route('/profile')
def user_profile():
    """User profile page."""
    return render_template('user_profile.html', user=mock_user)


@app.route('/profile/change-credentials', methods=['POST'])
def change_credentials():
    """Handle changing username and password."""
    # Placeholder for credential change logic
    # In production, this would update the database
    return redirect(url_for('user_profile'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
