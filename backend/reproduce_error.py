from app import app, db, User
import traceback

with app.test_client() as client:
    print("Testing /api/subjects without login...")
    try:
        response = client.get('/api/subjects')
        print(f"Status Code: {response.status_code}")
        print(f"Response Data: {response.get_json()}")
    except Exception:
        print("Exception during request:")
        traceback.print_exc()

    print("\nTesting /api/subjects with admin login simulation...")
    with app.app_context():
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            print("Admin user not found, creating one...")
            admin = User(username="admin", email="admin@school.edu", full_name="System Administrator", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
        admin_id = admin.id

    with client.session_transaction() as sess:
        sess['user_id'] = admin_id
    
    try:
        response = client.get('/api/subjects')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Success! Found {len(response.get_json())} subjects.")
        else:
            print(f"Error Response: {response.get_data(as_text=True)}")
    except Exception:
        print("Exception during logged-in request:")
        traceback.print_exc()
