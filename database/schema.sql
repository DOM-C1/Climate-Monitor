CREATE DATABASE weather;
\c weather

DROP TABLE air_quality;
DROP TABLE user_location_assignment;
DROP TABLE weather_alert;
DROP TABLE flood_warnings;
DROP TABLE forecast;
DROP TABLE weather_report;
DROP TABLE location;
DROP TABLE user_details;
DROP TABLE weather_code;
DROP TABLE alert_type;
DROP TABLE severity_level;
DROP TABLE county;
DROP TABLE country;

CREATE TABLE country(
    country_id SMALLINT NOT NULL UNIQUE GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(30) NOT NULL,
    PRIMARY KEY(country_id)
);

CREATE TABLE county(
    county_id SMALLINT NOT NULL UNIQUE GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(50) NOT NULL,
    country_id SMALLINT NOT NULL,
    PRIMARY KEY(county_id),
    CONSTRAINT fk_country
        FOREIGN KEY(country_id) 
            REFERENCES country(country_id)
);

CREATE TABLE severity_level(
    severity_level_id SMALLINT NOT NULL,
    severity_level VARCHAR(30) NOT NULL,
    PRIMARY KEY(severity_level_id)
);

CREATE TABLE alert_type(
    alert_type_id SMALLINT NOT NULL UNIQUE GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(30) NOT NULL,
    PRIMARY KEY(alert_type_id)
);

CREATE TABLE weather_code(
    weather_code_id SMALLINT NOT NULL,
    description VARCHAR(30) NOT NULL,
    PRIMARY KEY(weather_code_id)
);

CREATE TABLE location(
    loc_id INT NOT NULL UNIQUE GENERATED ALWAYS AS IDENTITY,
    longitude FLOAT NOT NULL,
    latitude FLOAT NOT NULL,
    loc_name VARCHAR(60) NOT NULL,
    county_id SMALLINT NOT NULL,
    PRIMARY KEY(loc_id),
    CONSTRAINT fk_county
        FOREIGN KEY(county_id) 
            REFERENCES county(county_id)
);

CREATE TABLE weather_report(
    weather_report_id BIGINT NOT NULL UNIQUE GENERATED ALWAYS AS IDENTITY,
    report_time TIMESTAMP NOT NULL,
    loc_id INT NOT NULL,
    PRIMARY KEY(weather_report_id),
    CONSTRAINT fk_location
        FOREIGN KEY(loc_id) 
            REFERENCES location(loc_id)
);

CREATE TABLE user_details(
    user_id SMALLINT NOT NULL UNIQUE GENERATED ALWAYS AS IDENTITY,
    email VARCHAR(70) UNIQUE NOT NULL,
    name VARCHAR(60) NOT NULL,
    password VARCHAR(40) NUT NULL,
    PRIMARY KEY(user_id)
);

CREATE TABLE forecast(
    forecast_id BIGINT NOT NULL UNIQUE GENERATED ALWAYS AS IDENTITY,
    forecast_timestamp TIMESTAMP NOT NULL,
    visibility SMALLINT NOT NULL,
    humidity SMALLINT NOT NULL,
    precipitation FLOAT NOT NULL,
    precipitation_prob SMALLINT NOT NULL,
    rainfall FLOAT NOT NULL,
    snowfall FLOAT NOT NULL,
    wind_speed FLOAT NOT NULL,
    wind_direction SMALLINT NOT NULL,
    wind_gusts FLOAT NOT NULL,
    lightning_potential SMALLINT NOT NULL,
    uv_index FLOAT NOT NULL,
    cloud_cover SMALLINT NOT NULL,
    temperature FLOAT NOT NULL,
    apparent_temp FLOAT NOT NULL,
    weather_report_id BIGINT NOT NULL,
    weather_code_id SMALLINT NOT NULL,
    PRIMARY KEY(forecast_id),
    CONSTRAINT fk_weather_report
        FOREIGN KEY(weather_report_id) 
            REFERENCES weather_report(weather_report_id),
    CONSTRAINT fk_weather_code
        FOREIGN KEY(weather_code_id) 
            REFERENCES weather_code(weather_code_id)
);

CREATE TABLE flood_warnings(
    flood_id BIGINT NOT NULL UNIQUE GENERATED ALWAYS AS IDENTITY,
    severity_level_id SMALLINT NULL,
    time_raised TIMESTAMP NOT NULL,
    loc_id INT NOT NULL,
    notified BOOLEAN DEFAULT FALSE,
    PRIMARY KEY(flood_id),
    CONSTRAINT fk_loc
        FOREIGN KEY(loc_id) 
            REFERENCES location(loc_id),
    CONSTRAINT fk_severity
        FOREIGN KEY(severity_level_id) 
            REFERENCES severity_level(severity_level_id)
);

CREATE TABLE weather_alert(
    alert_id BIGINT NOT NULL UNIQUE GENERATED ALWAYS AS IDENTITY,
    alert_type_id SMALLINT NOT NULL,
    forecast_id BIGINT NOT NULL,
    severity_level_id SMALLINT NOT NULL,
    notified BOOLEAN DEFAULT FALSE,
    PRIMARY KEY(alert_id),
    CONSTRAINT fk_forecast
        FOREIGN KEY(forecast_id) 
            REFERENCES forecast(forecast_id),
    CONSTRAINT fk_severity
        FOREIGN KEY(severity_level_id) 
            REFERENCES severity_level(severity_level_id)
);

CREATE TABLE air_quality(
    air_quality_id BIGINT NOT NULL UNIQUE GENERATED ALWAYS AS IDENTITY,
    o3_concentration SMALLINT NOT NULL,
    severity_level_id SMALLINT NOT NULL,
    weather_report_id SMALLINT NOT NULL,
    notified BOOLEAN DEFAULT FALSE,
    PRIMARY KEY(air_quality_id),
    CONSTRAINT fk_weather
        FOREIGN KEY(weather_report_id) 
            REFERENCES weather_report(weather_report_id),
    CONSTRAINT fk_severity
        FOREIGN KEY(severity_level_id) 
            REFERENCES severity_level(severity_level_id)
);

CREATE TABLE user_location_assignment(
    user_location_id INT NOT NULL UNIQUE GENERATED ALWAYS AS IDENTITY,
    user_id SMALLINT NOT NULL,
    loc_id INT NOT NULL,
    report_opt_in BOOLEAN NOT NULL,
    alert_opt_in BOOLEAN NOT NULL,
    PRIMARY KEY(user_location_id),
    CONSTRAINT fk_user
        FOREIGN KEY(user_id) 
            REFERENCES user_details(user_id),
    CONSTRAINT fk_location
        FOREIGN KEY(loc_id) 
            REFERENCES location(loc_id)
);
