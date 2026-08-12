# PropertyHub V2

Full-stack PostgreSQL version.

## Features
- PostgreSQL database
- Flask backend
- Responsive HTML/CSS/JS
- Resident dashboard
- Secretary dashboard
- Watchman dashboard
- Admin dashboard
- Property CRUD
- Complaint create/status management
- Amenity booking with unique date/slot protection
- Visitor registration/status
- User role management
- Rental search

## PostgreSQL setup

In SQL Shell / psql:
```sql
CREATE DATABASE propertyhub;
```

Then edit `.env.example` and use the values as environment variables, or set them in your terminal.

Windows example:
```powershell
$env:DB_NAME="propertyhub"
$env:DB_USER="postgres"
$env:DB_PASSWORD="YOUR_POSTGRES_PASSWORD"
```

Install and run:
```powershell
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Demo accounts
admin@propertyhub.com / admin123
secretary@propertyhub.com / secretary123
watchman@propertyhub.com / watchman123
resident@propertyhub.com / resident123

Change demo passwords before deployment.
