docker build -t my-python-app .
docker run --env-file .env -p 8080:8080 my-python-app