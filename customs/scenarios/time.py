from customs.scenarios.weather import WeatherBasicRoute

class TimeNight(WeatherBasicRoute):
    weather_config = {
        'sun_altitude_angle': -90.0
    }

class TimeDay(WeatherBasicRoute):
    weather_config = {
        'sun_altitude_angle': 45.0
    }

class TimeSunrise(WeatherBasicRoute):
    weather_config = {
        'sun_altitude_angle': 0.5
    }
