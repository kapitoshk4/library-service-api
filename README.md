# library-service-api

API Library service for borrowing books written on DRF and Dockerized.

# Installing using GitHub

Install PostgresSQL and create db.
```bash
git clone https://github.com/kapitoshk4/library-service-api.git
cd train_station
python -m venv venv
source venv/bin/activate
```
Copy .env.sample -> .env and populate with all required data
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
python manage.py createsuperuser
```
# Run with docker

```bash
docker-compose build
docker-compose up
docker-compose ps
docker exec -it your_image_name sh
- Create new admin user. `docker-compose run app sh -c "python manage.py createsuperuser`;
- Run tests using different approach: `docker-compose run web sh -c "python manage.py test"`;
```
# Getting access

To access the API endpoints, follow these steps:
1. Go to one if the following URLs:
   - [Login to obtain Token](http://127.0.0.1:8000/api/v1/user/register/) 
   - [Obtain Bearer token](http://127.0.0.1:8000/api/v1/user/token/)
2. Type your Email & Password. For example:
   - Email address: admin@admin.com
   - Password: 1qazcde3
3. After submitting your credentials, you will receive a token. This token grants access to the API endpoints.

# Available Endpoints For Users App

You can use the following endpoints:

- [Refresh Token](http://127.0.0.1:8000/api/v1/user/token/refresh/) - This URL will refresh your token when it expires.
- [Verify Token](http://127.0.0.1:8000/api/v1/user/token/verify/) - This URL will verify if your token is valid and has not expired.
- [User Details](http://127.0.0.1:8000/api/v1/user/me/) - This URL will display information about yourself using the token assigned to your user.

Please note that accessing certain endpoints may require the ModHeader extension, which is available for installation in Chrome.

That's it for user endpoints. You can now proceed to the next step.

# Getting Started With Api

1. First, go to the URL provided: [API Borrowing](http://127.0.0.1:8000/api/v1/borrowing/). This URL provides all borrowing endpoints of the API.
2. The URL for payments: [API Payments](http://127.0.0.1:8000/api/v1/payment/).
3. The URL for books: [API Payments](http://127.0.0.1:8000/api/v1/library/).
2. Now you are ready to use the API to manage your library service.

# Features
- JWT authentication
- Admin panel available at /admin/
- Documentation located at /api/v1/doc/swagger/
- Manage borrowings and payment, books for the library service
- Make borrowing and return them
- Make payment after borrowing
- FINE payment if borrowing is overdue
- Implemented filtering for every endpoint in Swagger
- Filtering Borrowings by: actual return date, users
