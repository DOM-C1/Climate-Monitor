echo "Connecting to DB"
export $(cat .env | xargs)
export PGPASSWORD=$DB_PASSWORD
psql --host=$DB_HOST --port=$DB_PORT --username=$DB_USER --dbname=weather -f dummy_data.sql