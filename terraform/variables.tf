variable "ACCESS_KEY_ID" {
    type = string
}

variable "SECRET_ACCESS_KEY" {
    type = string
}
variable "DB_USER" {
    type = string
    default = "postgres"
}
variable "DB_PASSWORD" {
    type = string
}
variable "DB_HOST" {
    type = string
}
variable "DB_NAME" {
    type = string
}
variable "DB_PORT" {
    type = number
}
variable "REGION" {
    type = string 
}
variable "SENDER_EMAIL" {
    type = string
}
variable "WEATHER_WARNING_TABLE" {
    type = string
}
variable "FLOOD_WARNING_TABLE" {
    type = string 
}
variable "AIR_QUALITY_TABLE" {
    type = string 
}