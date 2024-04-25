echo "Connecting to DB"
export $(cat .env | xargs)
export PGPASSWORD=$DB_PASSWORD
psql --host=$DB_HOST --port=$DB_PORT --username=$DB_USER --dbname=$DB_NAME -f schema.sql
python3 insert_metadata.py
psql --host=$DB_HOST --port=$DB_PORT --username=$DB_USER --dbname=$DB_NAME -f dummy_data.sql