from customs.scenarios.WeatherBasic import WeatherBasicRoute

class WeatherClear(WeatherBasicRoute):
    weather_config = {
        'cloudiness': 10.0,
        'precipitation': 0.0,
        'precipitation_deposits': 0.0,
        'wind_intensity': 5.0,
        'fog_density': 0.0,
        'fog_distance': 0.0,
        'fog_falloff': 0.2,
        'wetness': 0.0,
        'scattering_intensity': 0.0,
        'mie_scattering_scale': 0.0,
        'mie_scattering_scale': 0.0331,
    }

class WeatherOvercast(WeatherBasicRoute):
    weather_config = {
        'cloudiness': 80.0,
        'precipitation': 0.0,
        'precipitation_deposits': 0.0,
        'wind_intensity': 50.0,
        'fog_density': 2.0,
        'fog_distance': 0.75,
        'fog_falloff': 0.1,
        'wetness': 10.0,
        'scattering_intensity': 0.0,
        'mie_scattering_scale': 0.3,
        'mie_scattering_scale': 0.0331,
    }

class WeatherHardRain(WeatherBasicRoute):
    weather_config = {
        'cloudiness': 100.0,
        'precipitation': 80.0,
        'precipitation_deposits': 90.0,
        'wind_intensity': 100.0,
        'fog_density': 7.0,
        'fog_distance': 0.75,
        'fog_falloff': 0.1,
        'wetness': 100.0,
        'scattering_intensity': 0.0,
        'mie_scattering_scale': 0.3,
        'mie_scattering_scale': 0.0331,
    }