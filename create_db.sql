

DROP TABLE country;
DROP TABLE county;
DROP TABLE weather_code;
DROP TABLE location;
DROP TABLE weather_report;
DROP TABLE user;
DROP TABLE forecast;
DROP TABLE flood_warnings;
DROP TABLE alert_type;
DROP TABLE alert;
DROP TABLE cloud;
DROP TABLE temperature;
DROP TABLE sun;
DROP TABLE lightning_alert;
DROP TABLE wind;
DROP TABLE snow;
DROP TABLE rain;
DROP TABLE air;

CREATE TABLE weather_report(
    weather_report_id BIGINT NOT NULL UNIQUE GENERATED ALWAYS AS IDENTITY,
    report_time TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    loc_id SMALLINT NOT NULL,
    PRIMARY KEY(weather_report_id),
    CONSTRAINT fk_location
        FOREIGN KEY(loc_id) 
            REFERENCES location(loc_id)
);


CREATE TABLE temperature(
    temperature_id SMALLINT NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    apparent_temp DOUBLE PRECISION NOT NULL,
    forecast_id BIGINT NOT NULL,
    PRIMARY KEY(temperature_id),
    CONSTRAINT fk_forecast
        FOREIGN KEY(forecast_id) 
            REFERENCES forecast(forecast_id)
);

CREATE TABLE cloud(
    cloud_id BIGINT NOT NULL,
    cloud_cover SMALLINT NOT NULL,
    forecast_id BIGINT NOT NULL,
    PRIMARY KEY(cloud_id),
    CONSTRAINT fk_forecast
        FOREIGN KEY(forecast_id) 
            REFERENCES forecast(forecast_id)
);


CREATE TABLE alert_type(
    alert_type_id BIGINT NOT NULL,
    name VARCHAR(30) NOT NULL,
    PRIMARY KEY(alert_type_id),
);


CREATE TABLE weather_code(
    weather_code_id SMALLINT NOT NULL,
    description VARCHAR(30) NOT NULL,
    PRIMARY KEY(weather_code_id)
);


CREATE TABLE sun(
    sun_id BIGINT NOT NULL,
    uv_index DOUBLE PRECISION NOT NULL,
    forecast_id BIGINT NOT NULL,
    PRIMARY KEY(sun_id),
    CONSTRAINT fk_forecast
        FOREIGN KEY(forecast_id) 
            REFERENCES forecast(forecast_id)
);


CREATE TABLE flood_warnings(
    flood_id BIGINT NOT NULL,
    severity_level SMALLINT NULL,
    time_raised TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    forecast_id BIGINT NOT NULL,
    PRIMARY KEY(flood_id),
    CONSTRAINT fk_forecast
        FOREIGN KEY(forecast_id) 
            REFERENCES forecast(forecast_id)
);

CREATE TABLE lightning_alert(
    lightning_alert BIGINT NOT NULL,
    lightning_potential SMALLINT NOT NULL,
    forecast_id BIGINT NOT NULL,
    PRIMARY KEY(lightning_alert),
    CONSTRAINT fk_forecast
        FOREIGN KEY(forecast_id) 
            REFERENCES forecast(forecast_id)
);

CREATE TABLE alert(
    alert_id BIGINT NOT NULL,
    alert_type_id SMALLINT NOT NULL,
    forecast_id BIGINT NOT NULL,
    PRIMARY KEY(alert_id),
    CONSTRAINT fk_forecast
        FOREIGN KEY(forecast_id) 
            REFERENCES forecast(forecast_id),
    CONSTRAINT fk_alert_type
        FOREIGN KEY(alert_type_id) 
            REFERENCES alert(alert_type_id)
);

CREATE TABLE air(
    air_id BIGINT NOT NULL,
    air_quality SMALLINT NOT NULL,
    visibility SMALLINT NOT NULL,
    humidity SMALLINT NOT NULL,
    forecast_id BIGINT NOT NULL,
    PRIMARY KEY(air_id),
    CONSTRAINT fk_forecast
        FOREIGN KEY(forecast_id) 
            REFERENCES forecast(forecast_id)
);


CREATE TABLE forecast(
    forecast_id BIGINT NOT NULL,
    forecast_timestamp TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
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

CREATE TABLE snow(
    snow_id BIGINT NOT NULL,
    snowfall DOUBLE PRECISION NOT NULL,
    forecast_id BIGINT NOT NULL,
    PRIMARY KEY(snow_id),
    CONSTRAINT fk_forecast
        FOREIGN KEY(forecast_id) 
            REFERENCES forecast(forecast_id)
);


CREATE TABLE rain(
    rain_id BIGINT NOT NULL,
    precipitation DOUBLE PRECISION NOT NULL,
    precipitation_prob SMALLINT NOT NULL,
    rainfall SMALLINT NOT NULL,
    forecast_id BIGINT NOT NULL,
    PRIMARY KEY(rain_id),
    CONSTRAINT fk_forecast
        FOREIGN KEY(forecast_id) 
            REFERENCES forecast(forecast_id)
);


CREATE TABLE wind(
    wind_id BIGINT NOT NULL,
    wind_speed DOUBLE PRECISION NOT NULL,
    wind_direction SMALLINT NOT NULL,
    wind_gusts SMALLINT NOT NULL,
    forecast_id BIGINT NOT NULL,
    PRIMARY KEY(wind_id),
    CONSTRAINT fk_forecast
        FOREIGN KEY(forecast_id) 
            REFERENCES forecast(forecast_id)
);

CREATE TABLE location(
    loc_id SMALLINT NOT NULL,
    longitude VARCHAR(10) NOT NULL,
    latitude VARCHAR(10) NOT NULL,
    loc_name VARCHAR(60) NOT NULL,
    county_id SMALLINT NOT NULL,
    PRIMARY KEY(loc_id),
    CONSTRAINT fk_county
        FOREIGN KEY(county_id) 
            REFERENCES county(county_id)
);


CREATE TABLE county(
    county_id SMALLINT NOT NULL,
    name VARCHAR(30) NOT NULL,
    country_id SMALLINT NOT NULL,
    PRIMARY KEY(county_id),
    CONSTRAINT fk_country
        FOREIGN KEY(country_id) 
            REFERENCES country(country_id)
);

CREATE TABLE country(
    country_id SMALLINT NOT NULL,
    name VARCHAR(30) NOT NULL,
    PRIMARY KEY(country_id)
);

CREATE TABLE user(
    user_id SMALLINT NOT NULL,
    email VARCHAR(30) NOT NULL,
    loc_id SMALLINT NOT NULL,
    name VARCHAR(40) NOT NULL,
    CONSTRAINT fk_loc
        FOREIGN KEY(loc_id) 
            REFERENCES loc(loc_id)
);
