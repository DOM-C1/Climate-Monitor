terraform init
terraform apply
cp .env ../database/.env
cd ../database
source .env
export PGPASSWORD=$DB_PASSWORD
activate
psql --host=$DB_HOST --port=$DB_PORT --username=$DB_USER --dbname=postgres -f schema.sql
python insert_metadata.py
