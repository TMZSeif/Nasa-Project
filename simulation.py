from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import math

app = Flask(__name__)
CORS(app)

# Real asteroid data from NASA
ASTEROIDS = {
    "Sisyphus": {"diameter_km": 8.48, "spectral_type": "S", "density": 2500},
    "Sekhmet": {"diameter_km": 0.935, "spectral_type": "Unknown", "density": 2500},
    "Moshup": {"diameter_km": 1.317, "spectral_type": "S", "density": 2500},
    "Ishtar": {"diameter_km": 1.298, "spectral_type": "Unknown", "density": 2500},
    "Heracles": {"diameter_km": 4.843, "spectral_type": "O", "density": 3000},
    "Florence": {"diameter_km": 4.9, "spectral_type": "S", "density": 2500},
    "Dionysus": {"diameter_km": 1.5, "spectral_type": "Cb", "density": 2700},
    "Didymos": {"diameter_km": 0.78, "spectral_type": "S", "density": 2500},
    "Apollo": {"diameter_km": 1.5, "spectral_type": "Q", "density": 2500}
}

LOCATIONS = {
    "Tokyo": {"lat": 35.6762, "lon": 139.6503, "population": 37400000, "country": "Japan", "area": "8,547 km²"},
    "Berlin": {"lat": 52.5200, "lon": 13.4050, "population": 3645000, "country": "Germany", "area": "891 km²"},
    "Sao Paulo": {"lat": -23.5505, "lon": -46.6333, "population": 12300000, "country": "Brazil", "area": "7,946 km²"},
    "London": {"lat": 51.5074, "lon": -0.1278, "population": 9000000, "country": "United Kingdom", "area": "8,382 km²"},
    "Moscow": {"lat": 55.7558, "lon": 37.6173, "population": 12500000, "country": "Russia", "area": "5,891 km²"},
    "New York": {"lat": 40.7128, "lon": -74.0060, "population": 18800000, "country": "United States", "area": "11,875 km²"},
    "Paris": {"lat": 48.8566, "lon": 2.3522, "population": 10900000, "country": "France", "area": "17,174 km²"}
}

def calculate_impact_energy(diameter_km, velocity_km_s, density_kg_m3):
    radius_m = (diameter_km * 1000) / 2
    volume_m3 = (4/3) * math.pi * (radius_m ** 3)
    mass_kg = volume_m3 * density_kg_m3
    velocity_m_s = velocity_km_s * 1000
    energy_joules = 0.5 * mass_kg * (velocity_m_s ** 2)
    energy_megatons = energy_joules / 4.184e15
    return energy_megatons

def calculate_psi_radius(energy_megatons, psi_value):
    if psi_value == 20:
        C = 0.28
    elif psi_value == 3:
        C = 1.04
    else:
        C = 1.0
    radius_km = C * (energy_megatons ** (1/3))
    return radius_km

def estimate_affected_population(radius_km, city_data):
    city_population = city_data['population']
    city_area_km2 = math.pi * (50 ** 2)
    impact_area_km2 = math.pi * (radius_km ** 2)
    if impact_area_km2 < city_area_km2:
        affected = city_population * (impact_area_km2 / city_area_km2)
    else:
        affected = city_population
    return int(affected)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulation</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-image: url('https://i.postimg.cc/JzhSpp47/starry-night-wallpaper-98d7331900085cd1637177b600354afb.jpg');
            background-repeat: no-repeat;
            background-size: 200%;
            color: #e8e8e8;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            text-align: center;
            padding: 30px 20px;
            background: #1a1a1a;
            border-radius: 12px;
            margin-bottom: 30px;
            border: 1px solid #333;
        }

        h1 {
            font-size: 3em;
            color: #fff;
            margin-bottom: 10px;
            font-weight: 700;
            letter-spacing: 2px;
        }

        .subtitle {
            font-size: 1.1em;
            color: #999;
        }

        .main-layout {
            display: flex;
            flex-direction: column;
            gap: 25px;
            margin-bottom: 30px;
        }

        .controls-row {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            background: #1a1a1a;
            border-radius: 12px;
            padding: 25px;
            border: 1px solid #333;
        }

        .control-group {
            display: flex;
            flex-direction: column;
        }

        .control-group label {
            margin-bottom: 8px;
            font-weight: 500;
            color: #ccc;
            font-size: 0.95em;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .tooltip {
            position: relative;
            display: inline-block;
            cursor: help;
        }

        .tooltip-icon {
            width: 18px;
            height: 18px;
            background: #444;
            color: #fff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
        }

        .tooltip:hover .tooltip-icon {
            background: #666;
        }

        .tooltip-text {
            visibility: hidden;
            width: 280px;
            background: #2a2a2a;
            color: #e8e8e8;
            text-align: center;
            border-radius: 8px;
            padding: 12px;
            position: absolute;
            z-index: 1000;
            bottom: 125%;
            left: 50%;
            margin-left: -140px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.85em;
            line-height: 1.4;
            border: 1px solid #444;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }

        .tooltip-text::after {
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #2a2a2a transparent transparent transparent;
        }

        .tooltip:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }

        select {
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #444;
            background: #0d0d0d;
            color: #e8e8e8;
            font-size: 1em;
            cursor: pointer;
        }

        select:hover {
            border-color: #666;
        }

        select:focus {
            outline: none;
            border-color: #888;
        }

        select option {
            background: #1a1a1a;
            color: #fff;
        }

        .info-box {
            margin-top: 10px;
            padding: 12px;
            background: #0d0d0d;
            border-radius: 8px;
            border: 1px solid #333;
            font-size: 0.9em;
            display: none;
        }

        .info-box.active {
            display: block;
        }

        .info-box strong {
            color: #fff;
        }

        input[type="range"] {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: linear-gradient(to right, #333, #666);
            outline: none;
            -webkit-appearance: none;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #fff;
            cursor: pointer;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
        }

        input[type="range"]::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #fff;
            cursor: pointer;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
            border: none;
        }

        .speed-display {
            text-align: center;
            margin: 10px 0;
            font-size: 1.8em;
            color: #fff;
            font-weight: bold;
        }

        .simulate-section {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
        }

        .simulate-btn {
            padding: 15px 40px;
            background: #fff;
            border: none;
            border-radius: 10px;
            color: #000;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }

        .simulate-btn:hover {
            background: #f0f0f0;
            transform: translateY(-2px);
        }

        .simulate-btn:disabled {
            background: #555;
            color: #888;
            cursor: not-allowed;
        }

        #map {
            height: 650px;
            border-radius: 12px;
            border: 2px solid #333;
            display: none;
        }

        #map.active {
            display: block;
        }

        .map-placeholder {
            height: 650px;
            border-radius: 12px;
            border: 2px dashed #444;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            background: #1a1a1a;
        }

        .map-placeholder.hidden {
            display: none;
        }

        .placeholder-content {
            text-align: center;
            color: #666;
        }

        .placeholder-content h3 {
            font-size: 2em;
            margin-bottom: 15px;
            color: #999;
        }

        .results-panel {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 25px;
            border: 1px solid #333;
            margin-top: 25px;
            display: none;
        }

        .results-panel.active {
            display: block;
        }

        .results-panel h3 {
            margin-bottom: 20px;
            color: #fff;
            font-size: 1.8em;
        }

        .result-item {
            margin-bottom: 15px;
            padding: 15px;
            background: #0d0d0d;
            border-radius: 8px;
            border-left: 4px solid #fff;
        }

        .result-item strong {
            color: #fff;
        }

        .damage-zone {
            margin: 10px 0;
            padding: 15px;
            border-radius: 8px;
        }

        .damage-zone.severe {
            border-left: 4px solid #fff;
            background: rgba(255, 255, 255, 0.05);
        }

        .damage-zone.moderate {
            border-left: 4px solid #888;
            background: rgba(136, 136, 136, 0.05);
        }

        .damage-zone h4 {
            margin-bottom: 10px;
            color: #fff;
        }

        .research-btn {
            width: 100%;
            padding: 12px;
            background: #2a2a2a;
            border: 1px solid #444;
            border-radius: 10px;
            color: #e8e8e8;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            margin-top: 30px;
            max-width: 400px;
            display: block;
            margin-left: auto;
            margin-right: auto;
            transition: all 0.3s;
        }

        .research-btn:hover {
            background: #333;
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            overflow-y: auto;
        }

        .modal.active {
            display: block;
        }

        .modal-content {
            background: #1a1a1a;
            margin: 50px auto;
            padding: 40px;
            border-radius: 15px;
            max-width: 800px;
            border: 1px solid #333;
        }

        .close-btn {
            float: right;
            font-size: 2em;
            font-weight: bold;
            cursor: pointer;
            color: #fff;
        }

        .close-btn:hover {
            color: #ccc;
        }

        .research-section {
            margin: 20px 0;
        }

        .research-section h3 {
            color: #fff;
            margin-bottom: 10px;
            font-size: 1.5em;
        }

        .research-section h4 {
            color: #ccc;
            margin-top: 15px;
            margin-bottom: 8px;
        }

        .research-section ul {
            margin-left: 20px;
            line-height: 1.8;
        }

        .research-section p {
            line-height: 1.8;
            margin-bottom: 10px;
        }

        .impact-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
            display: none;
        }

        .impact-animation.active {
            display: block;
        }

        .meteor {
            position: absolute;
            width: 50px;
            height: 50px;
            background: radial-gradient(circle, #fff, #ccc);
            border-radius: 50%;
            box-shadow: 0 0 20px #fff;
            opacity: 0;
        }

        .meteor.falling {
            animation: meteorFall 1.5s ease-in forwards;
        }

        @keyframes meteorFall {
            0% {
                opacity: 0;
                transform: translate(-200px, -200px) scale(0.5);
            }
            20% {
                opacity: 1;
            }
            100% {
                opacity: 1;
                transform: translate(0, 0) scale(1);
            }
        }

        .impact-flash {
            position: absolute;
            width: 150px;
            height: 150px;
            background: radial-gradient(circle, rgba(255,255,255,1), transparent);
            border-radius: 50%;
            opacity: 0;
        }

        .impact-flash.active {
            animation: flash 0.5s ease-out;
        }

        @keyframes flash {
            0% {
                opacity: 0;
                transform: scale(0);
            }
            50% {
                opacity: 1;
                transform: scale(1);
            }
            100% {
                opacity: 0;
                transform: scale(2);
            }
        }

        @media (max-width: 1024px) {
            .controls-row {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>SIMULATION</h1>
            <!-- <p class="subtitle">Asteroid Impact Simulator</p> -->
        </header>
        <audio id="explosion"><source src="https://audio.jukehost.co.uk/BkJrT8bymF3AbLFOfvIpxpP711oO67Cl"></audio>
        <div class="main-layout">
            <div class="controls-row">
                <div class="control-group">
                    <label>
                        Select Asteroid
                        <span class="tooltip">
                            <span class="tooltip-icon">?</span>
                            <span class="tooltip-text">Real near-Earth asteroids that have made close approaches to our planet throughout history</span>
                        </span>
                    </label>
                    <select id="asteroid-select">
                        <option value="">-- Choose Asteroid --</option>
                    </select>
                    <div class="info-box" id="asteroid-info">
                        <strong>Diameter:</strong> <span id="asteroid-diameter"></span><br>
                        <strong>Type:</strong> <span id="asteroid-type"></span>
                    </div>
                </div>

                <div class="control-group">
                    <label>
                        Impact Location
                        <span class="tooltip">
                            <span class="tooltip-icon">?</span>
                            <span class="tooltip-text">Some of the most popular cities in the world</span>
                        </span>
                    </label>
                    <select id="location-select">
                        <option value="">-- Choose City --</option>
                    </select>
                    <div class="info-box" id="city-info">
                        <strong>Country:</strong> <span id="city-country"></span><br>
                        <strong>Population:</strong> <span id="city-population"></span><br>
                        <strong>Metro Area:</strong> <span id="city-area"></span>
                    </div>
                </div>

                <div class="control-group">
                    <label>
                        Impact Velocity
                        <span class="tooltip">
                            <span class="tooltip-icon">?</span>
                            <span class="tooltip-text">Typical asteroid impact velocities range from 10 to 70 km/s depending on orbital trajectory and entry angle</span>
                        </span>
                    </label>
                    <div class="speed-display"><span id="velocity-value">40</span> km/s</div>
                    <input type="range" id="velocity-slider" min="10" max="70" step="10" value="40">
                    <div class="simulate-section">
                        <button class="simulate-btn" id="simulate-btn">SIMULATE IMPACT</button>
                    </div>
                </div>
            </div>

            <div class="map-section">
                <div class="map-placeholder" id="map-placeholder">
                    <div class="placeholder-content">
                        <h3>Ready to Simulate</h3>
                        <p>Select an asteroid, location, and velocity above</p>
                    </div>
                </div>
                <div id="map"></div>
            </div>
        </div>

        <div class="results-panel" id="results-panel">
            <h3>Impact Analysis Results</h3>
            <div id="results-content"></div>
        </div>
        <p>Some numbers may be inaccurate*</p>
        <button class="research-btn" id="research-btn">Back to Homepage</button>
    </div>

    <div class="impact-animation" id="impact-animation">
        <div class="meteor" id="meteor"></div>
        <div class="impact-flash" id="impact-flash"></div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const API_URL = window.location.origin;
        
        let map;
        let markers = {};
        let circles = {};

        function initMap() {
            map = L.map('map').setView([20, 0], 2);
            
            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Esri',
                maxZoom: 18
            }).addTo(map);

            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png', {
                maxZoom: 18,
                opacity: 0.7
            }).addTo(map);
        }

        async function loadData() {
            try {
                const asteroidsRes = await fetch(API_URL + '/api/asteroids');
                const locationsRes = await fetch(API_URL + '/api/locations');
                
                const asteroids = await asteroidsRes.json();
                const locations = await locationsRes.json();
                
                addLocationMarkers(locations);
            } catch (error) {
                console.error('Error loading map markers:', error);
            }
        }

        function addLocationMarkers(locations) {
            const cityIcon = L.divIcon({
                className: 'custom-marker',
                html: '💥',
                iconSize: [30, 30],
                iconAnchor: [15, 30]
            });

            for (const cityName in locations) {
                if (locations.hasOwnProperty(cityName)) {
                    const cityData = locations[cityName];
                    const marker = L.marker([cityData.lat, cityData.lon], { icon: cityIcon })
                        .addTo(map)
                        .bindPopup('<b>' + cityName + '</b>');
                    markers[cityName] = marker;
                }
            };
            }

        document.getElementById('velocity-slider').addEventListener('input', function(e) {
            document.getElementById('velocity-value').textContent = e.target.value;
        });

        // Asteroid info
        document.getElementById('asteroid-select').addEventListener('change', function(e) {
            const asteroidName = e.target.value;
            const infoBox = document.getElementById('asteroid-info');
            
            if (!asteroidName) {
                infoBox.classList.remove('active');
                return;
            }

            fetch(API_URL + '/api/simulate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ asteroid: asteroidName, location: 'Tokyo', velocity: 40 })
            })
            .then(response => response.json())
            .then(details => {
                document.getElementById('asteroid-diameter').textContent = details.asteroid_info.diameter_km + ' km';
                document.getElementById('asteroid-type').textContent = details.asteroid_info.spectral_type || 'Unknown';
                infoBox.classList.add('active');
            })
            .catch(error => console.error('Error:', error));
        });

        // City info
        document.getElementById('location-select').addEventListener('change', function(e) {
            const cityName = e.target.value;
            const cityInfoBox = document.getElementById('city-info');
            
            if (!cityName) {
                cityInfoBox.classList.remove('active');
                return;
            }

            fetch(API_URL + '/api/locations')
            .then(response => response.json())
            .then(locations => {
                const cityData = locations[cityName];
                if (cityData) {
                    document.getElementById('city-country').textContent = cityData.country;
                    document.getElementById('city-population').textContent = (cityData.population / 1000000).toFixed(1) + ' million';
                    document.getElementById('city-area').textContent = cityData.area;
                    cityInfoBox.classList.add('active');
                }
            })
            .catch(error => console.error('Error:', error));
        });

        document.getElementById('simulate-btn').addEventListener('click', function() {
            const asteroid = document.getElementById('asteroid-select').value;
            const location = document.getElementById('location-select').value;
            const velocity = parseInt(document.getElementById('velocity-slider').value);

            if (!asteroid || !location) {
                alert('Please select both an asteroid and a location!');
                return;
            }

            document.getElementById('map').classList.add('active');
            document.getElementById('map-placeholder').classList.add('hidden');

            if (!map) {
                initMap();
                loadData();
            }

            const btn = document.getElementById('simulate-btn');
            btn.textContent = 'CALCULATING...';
            btn.disabled = true;

            fetch(API_URL + '/api/simulate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ asteroid: asteroid, location: location, velocity: velocity })
            })
            .then(response => response.json())
            .then(result => {
                setTimeout(function() {
                    document.getElementById('map').scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 200);
                
                setTimeout(function() {
                    playImpactAnimation(result.coordinates);
                }, 1000);

                setTimeout(function() {
                    displayResults(result);
                    drawDamageZones(result);
                    const explosion = document.getElementById('explosion');
                    explosion.play();
                }, 2600);

                btn.textContent = 'SIMULATE IMPACT';
                btn.disabled = false;
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error simulating impact');
                btn.textContent = 'SIMULATE IMPACT';
                btn.disabled = false;
            });
        });

        function playImpactAnimation(coords) {
            const animContainer = document.getElementById('impact-animation');
            const meteor = document.getElementById('meteor');
            const flash = document.getElementById('impact-flash');

            const mapEl = document.getElementById('map');
            const rect = mapEl.getBoundingClientRect();
            
            const targetX = rect.left + rect.width / 2;
            const targetY = rect.top + rect.height / 2;

            meteor.style.left = targetX + 'px';
            meteor.style.top = targetY + 'px';
            flash.style.left = (targetX - 75) + 'px';
            flash.style.top = (targetY - 75) + 'px';

            animContainer.classList.add('active');
            meteor.classList.add('falling');

            setTimeout(function() {
                flash.classList.add('active');
            }, 1500);

            setTimeout(function() {
                animContainer.classList.remove('active');
                meteor.classList.remove('falling');
                flash.classList.remove('active');
            }, 2500);
        }

        function displayResults(result) {
            const severeArea = Math.PI * Math.pow(result.damage_zones.severe.radius_km, 2);
            const moderateArea = Math.PI * Math.pow(result.damage_zones.moderate.radius_km, 2);
            const hiroshimaMultiplier = Math.round(result.energy_megatons / 0.015);
            const craterDiameter = (result.asteroid_info.diameter_km * 20).toFixed(1);
            
            const htmlContent = '<div class="result-item">' +
                '<p><strong>Asteroid:</strong> ' + result.asteroid + ' (' + result.asteroid_info.diameter_km + ' km diameter)</p>' +
                '<p><strong>Impact Location:</strong> ' + result.location + '</p>' +
                '<p><strong>Impact Velocity:</strong> ' + result.velocity_km_s + ' km/s</p>' +
                '<p><strong>Impact Energy:</strong> ' + result.energy_megatons.toLocaleString() + ' megatons of TNT (that is ' + hiroshimaMultiplier.toLocaleString() + 'x the Hiroshima Bomb!)</p>' +
                '<p><strong>Crater Diameter:</strong> Approximately ' + craterDiameter + ' km</p>' +
                '</div>' +
                '<div class="damage-zone severe">' +
                '<h4>SEVERE DAMAGE ZONE (20 PSI)</h4>' +
                '<p><strong>Radius:</strong> ' + result.damage_zones.severe.radius_km + ' km</p>' +
                '<p><strong>Area Affected:</strong> ' + severeArea.toFixed(1) + ' km²</p>' +
                '<p><strong>Effects:</strong> ' + result.damage_zones.severe.description + '</p>' +
                '<p><strong>Estimated Casualties:</strong> ' + result.damage_zones.severe.estimated_affected.toLocaleString() + ' people</p>' +
                '</div>' +
                '<div class="damage-zone moderate">' +
                '<h4>MODERATE DAMAGE ZONE (3 PSI)</h4>' +
                '<p><strong>Radius:</strong> ' + result.damage_zones.moderate.radius_km + ' km</p>' +
                '<p><strong>Area Affected:</strong> ' + moderateArea.toFixed(1) + ' km²</p>' +
                '<p><strong>Effects:</strong> ' + result.damage_zones.moderate.description + '</p>' +
                '<p><strong>Estimated Casualties:</strong> ' + result.damage_zones.moderate.estimated_affected.toLocaleString() + ' people</p>' +
                '</div>';
            
            document.getElementById('results-content').innerHTML = htmlContent;
            document.getElementById('results-panel').classList.add('active');
        }

        function drawDamageZones(result) {
            Object.values(circles).forEach(function(c) { map.removeLayer(c); });
            circles = {};

            const coords = [result.coordinates.lat, result.coordinates.lon];
            map.flyTo(coords, 9, {duration: 1.5});

            setTimeout(function() {
                circles.moderate = L.circle(coords, {
                    color: '#888',
                    fillColor: '#666',
                    fillOpacity: 0.2,
                    weight: 2,
                    radius: result.damage_zones.moderate.radius_km * 1000
                }).addTo(map).bindPopup('3 PSI Zone<br>' + result.damage_zones.moderate.radius_km + ' km');

                circles.severe = L.circle(coords, {
                    color: '#fff',
                    fillColor: '#444',
                    fillOpacity: 0.3,
                    weight: 2,
                    radius: result.damage_zones.severe.radius_km * 1000
                }).addTo(map).bindPopup('20 PSI Zone<br>' + result.damage_zones.severe.radius_km + ' km');

                
            }, 500);
        }

        document.getElementById('research-btn').addEventListener('click', function() {
            console.log(window.location.href.split("/")[2])
            window.location.href = "/"
        });

        window.addEventListener('load', function() {
            console.log('Page loaded!');
            console.log('API_URL is:', API_URL);
            
            var asteroidSelect = document.getElementById('asteroid-select');
            var locationSelect = document.getElementById('location-select');
            
            console.log('Asteroid select found:', asteroidSelect);
            console.log('Location select found:', locationSelect);
            
            if (!asteroidSelect || !locationSelect) {
                alert('ERROR: Dropdown elements not found!');
                return;
            }
            
            setTimeout(function() {
                loadAsteroidsAndLocations();
            }, 500);
        });

        function loadAsteroidsAndLocations() {
            console.log('Starting to load data...');
            console.log('API URL:', API_URL);
            
            // Load asteroids
            fetch(API_URL + '/api/asteroids')
            .then(function(response) { 
                console.log('Asteroids response:', response);
                if (!response.ok) throw new Error('Asteroids API failed');
                return response.json(); 
            })
            .then(function(asteroids) {
                console.log('Asteroids data received:', asteroids);
                const select = document.getElementById('asteroid-select');
                
                if (!select) {
                    console.error('Asteroid select element not found!');
                    return;
                }
                
                asteroids.forEach(function(asteroid) {
                    const option = document.createElement('option');
                    option.value = asteroid;
                    option.textContent = asteroid;
                    select.appendChild(option);
                });
                console.log('Added ' + asteroids.length + ' asteroids to dropdown');
            })
            .catch(function(error) { 
                console.error('Error loading asteroids:', error);
                alert('Error loading asteroids: ' + error.message);
            });

            // Load locations
            fetch(API_URL + '/api/locations')
            .then(function(response) { 
                console.log('Locations response:', response);
                if (!response.ok) throw new Error('Locations API failed');
                return response.json(); 
            })
            .then(function(locations) {
                console.log('Locations data received:', locations);
                const select = document.getElementById('location-select');
                
                if (!select) {
                    console.error('Location select element not found!');
                    return;
                }
                
                Object.keys(locations).forEach(function(location) {
                    const option = document.createElement('option');
                    option.value = location;
                    option.textContent = location;
                    select.appendChild(option);
                });
                console.log('Added ' + Object.keys(locations).length + ' locations to dropdown');
            })
            .catch(function(error) { 
                console.error('Error loading locations:', error);
                alert('Error loading locations: ' + error.message);
            });
        }
    </script>
</body>
</html>
"""

HTML_WELCOME = """
<!DOCTYPE html>
<html lang="en">

<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Meteor Madness</title>
	<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
	<link href="https://fonts.googleapis.com/css2?family=Sterion&display=swap" rel="stylesheet">
	<style>
		* {
			margin: 0;
			padding: 0;
			box-sizing: border-box;

		}

		body {
			font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
			/* background: #0d0d0d; */
			color: #e8e8e8;
			min-height: 100vh;
			background-image: url('https://i.postimg.cc/qvqThb8T/5bd334f8d938f-wallpaper-c8c6bd88f0c0cc28504cf1ae8872543a.jpg');
			background-repeat: no-repeat;
			background-size:110%;
			background-position: center;
		}

		.container {
			max-width: 1400px;
			margin: 0 auto;
			padding: 20px;
		}

		.start-container {
			display: flex;
			flex-direction: column;
			column-gap: 5px;
			justify-content: center;
			align-items: center;
			padding-top: 150px;
			height: 100vh;
		}

		header {
			text-align: center;
			padding: 30px 20px;
			background: #1a1a1a;
			border-radius: 12px;
			margin-bottom: 30px;
			border: 1px solid #333;
		}

		h1 {
			font-size: 3em;
			color: #fff;
			margin-bottom: 10px;
			font-weight: 700;
			letter-spacing: 2px;
		}

		
		.welcome-btn:hover {
			background: #1d1d1d;
		}

		.welcome-btn {
			width: 100%;
			padding: 12px;
			background: #2b2bfd;
			border: 1px solid #444;
			border-radius: 10px;
			color: #e8e8e8;
			font-size: 1em;
			font-weight: bold;
			cursor: pointer;
			margin-top: 8px;
			max-width: 200px;
			display: block;
			margin-left: auto;
			margin-right: auto;
			transition: all 0.3s;
		}

        .name {
            font-size: 80px;
            margin: 0;
            padding: 0;
            margin-bottom: 250px;
            letter-spacing: 15px;
            color: #999999
        }
	</style>
</head>

<body>
	<div class="start-container">
        <h1 class="name">EGYPTEROIDS</h1>
		<button id="start-btn" onclick="startredirect()" class="welcome-btn">Simulate</button>
        <button id="about-btn" onclick="gameredirect()" class="welcome-btn">Game</button>
        <button id="about-btn" onclick="aboutredirect()" class="welcome-btn">About</button>
	</div>
</body>
<script>
	startredirect = () => {
		window.location.href = "/simulation"
	}
	aboutredirect = () => {
		window.location.href = "/about"
	}
    gameredirect = () => {
        window.location.href = "/game"
    }
</script>
</html>
"""

HTML_ABOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meteor Madness</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-image: url('https://i.postimg.cc/JzhSpp47/starry-night-wallpaper-98d7331900085cd1637177b600354afb.jpg');
            background-repeat: no-repeat;
            background-size: 150%;
            color: #e8e8e8;
            min-height: 100vh;
        }

        .container {
            margin: 0 auto;
        }

        header {
            text-align: center;
            padding: 30px 20px;
            background: #1a1a1a;
            border-radius: 12px;
            margin-bottom: 30px;
            border: 1px solid #333;
        }

        h1 {
            font-size: 3em;
            color: #fff;
            margin-bottom: 10px;
            font-weight: 700;
            letter-spacing: 2px;
        }

        .research-btn {
            width: 100%;
            padding: 12px;
            background: #2a2a2a;
            border: 1px solid #444;
            border-radius: 10px;
            color: #e8e8e8;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            margin-top: 30px;
            margin-bottom: 30px;
            max-width: 400px;
            display: block;
            margin-left: auto;
            margin-right: auto;
            transition: all 0.3s;
        }

        .research-btn:hover {
            background: #333;
        }

        .about-header {
            padding-left: 20px;
        }
        .about-text {
            padding-left: 40px;
            font-size: 25px;
        }
        ul {
            list-style-type: none !important;
        }
        .assumption {
            padding-bottom: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="about-header">Our team</h1>
        <p class="about-text">We are a team of Egyptian A Level students. We came together to create this project for Nasa Space Apps 2025!</p>
        <h1 class="about-header">Team Members</h1>
        <ul>
            <li class="about-text">●  Seif Tamer</li>
            <li class="about-text">●  Abdelrahman Abdelhafez</li>
            <li class="about-text">●  Moaaz Mohamed</li>
        </ul>
        <br>
        <br>
        <h1 class="about-header">Assumptions</h1>
        <p class="about-text assumption">We assumed that: </p>
        <ul>
            <li class="about-text">●  The impact angle is always 90°</li>
            <li class="about-text">●  The asteroids are perfectly spherical</li>
            <li class="about-text">●  The sea level impact is at standard elevation</li>
            <li class="about-text">●  Unknown Asteroid spectral types are assumed to have a density of 2500</li>
        </ul>
        <br>
        <br>
        <h1 class="about-header">Physics and Mathematics: </h1>
        <ul>
            <li class="about-text">●  Kinetic Energy Formula: E = ½ × m × v²</li>
            <li class="about-text">●  Blast Scaling Formula: R = C × Y^(1/3) (where C = 0.28 for 20 PSI, C = 1.04 for 3 PSI)</li>
        </ul>
        <br>
        <br>
        <h1 class="about-header">Damage Zones: </h1>
        <ul>
            <li class="about-text">20 PSI (Severe): Complete building destruction, near 100% casualties</li>
            <li class="about-text">3 PSI (Moderate): Severe structural damage, ~50% casualties</li>
        </ul>
        <br>
        <br>
        <br>
        <p>Some formulas and coding were done by the help of Artificial Intelligence*</p>
        <button class="research-btn" onclick="home()" id="research-btn">Back to Homepage</button>
    </div>
</body>
<script>
    home = () => {
        window.location.href = "/"
    }
</script>
</html>
"""

HTML_GAME = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Space Shooter - Defend Earth</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background-image: url('https://i.postimg.cc/0jtG6XdT/wallpaperflare-com-wallpaper.jpg');
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center center;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            font-family: 'Courier New', monospace;
            overflow: hidden;
        }

        #gameContainer {
            position: relative;
            background: rgba(0, 0, 0, 0.4);
        }

        #gameCanvas {
            display: block;
            background-color: transparent;
        }

        #ui {
            position: absolute;
            top: 20px;
            left: 20px;
            color: rgb(40, 122, 184);
            font-size: 20px;
            font-weight: bold;
            z-index: 10;
        }

        #gameOver {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: #f00;
            font-size: 48px;
            font-weight: bold;
            display: none;
            z-index: 20;
        }

        #gameOver button {
            margin-top: 20px;
            padding: 15px 40px;
            font-size: 24px;
            background: rgb(24, 74, 112);
            color: #000;
            border: none;
            cursor: pointer;
            font-family: 'Courier New', monospace;
            font-weight: bold;
        }

        #gameOver button:hover {
            background: rgb(40, 114, 171);
        }
		.start-btn {
            width: 100%;
            padding: 12px;
            background: #2a2a2a;
            border: 1px solid #444;
            border-radius: 10px;
            color: #e8e8e8;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            margin-top: 30px;
            margin-bottom: 30px;
            max-width: 400px;
            display: block;
            margin-left: auto;
            margin-right: auto;
            transition: all 0.3s;
        }

        .start-btn:hover {
            background: #333;
        }

        .text {
            z-index: 999;
            color: white;
        }
    </style>
</head>

<body>
    <div id="gameContainer">
        <audio id="shoot"><source src="https://audio.jukehost.co.uk/0udu8JtiOvJh8S6tBUcb5VzIYpxugUkW"></audio>
        <audio id="dead"><source src="https://audio.jukehost.co.uk/aJfL2L1SBEbRClq11OFOhuXEIewttjCb"></audio>
        <audio id="explosion"><source src="https://audio.jukehost.co.uk/lcjH1tRLuvQUBjTT7Vel4tywgQGx1zuw"></audio>
        <canvas id="gameCanvas" width="800" height="600"></canvas>
        <h3 class="text">Try to defend the Earth from the different Asteroids (the ones in the simulation page!)</h3>
        <h5 class="text">Please shoot one bullet at a time*</h5>
        <div id="ui">
            <div>Score: <span id="score">0</span></div>
            <div>Health: <span id="health">100</span></div>
        </div>
        <div id="gameOver">
            <div>GAME OVER</div>
            <div style="font-size: 24px; margin-top: 10px;">Final Score: <span id="finalScore">0</span></div>
            <button onclick="restartGame()">PLAY AGAIN</button>
        </div>
		<button id="home" onclick="home()" class="start-btn">Return to Homepage</button>
    </div>
    <script>
		home = () => {
			window.location.href = "/"
		}
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const container = document.getElementById('gameContainer');

        const playerImage = new Image();
        playerImage.src = 'https://i.postimg.cc/7h0gt59L/battle-ship-pixels-vintage-technology-isolated-icon-vector-removebg-preview.png';

        let gameActive = true;
        let score = 0;
        let health = 100;
        let mouseX = canvas.width / 2;
        let mouseY = canvas.height / 2;
        let mouseDown = false;

        const player = {
            x: canvas.width / 2 - 20,
            y: canvas.height - 80,
            w: 60,
            h: 75,
            speed: 0.15,
        };

        let bullets = [];
        let meteors = [];
        let lastShot = 0;
        let meteorSpawnRate = 1000;
        let lastMeteorSpawn = 0;

        canvas.addEventListener('mousemove', (e) => {
            const rect = canvas.getBoundingClientRect();
            mouseX = e.clientX - rect.left;
            mouseY = e.clientY - rect.top;
        });

        canvas.addEventListener('mousedown', (e) => {
            if (gameActive) {
                mouseDown = true;
            }
            shoot = document.getElementById('shoot');
            shoot.play()
        });

        canvas.addEventListener('mouseup', (e) => {
            mouseDown = false;
        });

        canvas.addEventListener('mouseleave', (e) => {
            mouseDown = false;
        });

        function shootBullet() {
            const now = Date.now();
            if (now - lastShot > 200) {
                bullets.push({
                    x: player.x + player.w / 2 - 2,
                    y: player.y,
                    w: 4,
                    h: 15,
                    speed: 8
                });
                lastShot = now;
            }
        }

        function spawnMeteor() {
            const size = Math.random() * 30 + 20;
            meteors.push({
                x: Math.random() * (canvas.width - size),
                y: -size,
                w: size,
                h: size,
                speed: Math.random() * 2 + 1,
                rotation: Math.random() * Math.PI * 2,
                rotSpeed: (Math.random() - 0.5) * 0.1
            });
        }

        function drawPlayer() {
            if (playerImage.complete) {
                ctx.drawImage(playerImage, player.x, player.y, player.w, player.h);
            } else {
                ctx.fillStyle = player.color;
                ctx.beginPath();
                ctx.moveTo(player.x + player.w / 2, player.y);
                ctx.lineTo(player.x, player.y + player.h);
                ctx.lineTo(player.x + player.w / 2, player.y + player.h - 10);
                ctx.lineTo(player.x + player.w, player.y + player.h);
                ctx.closePath();
                ctx.fill();
            }
        }

        function drawBullet(b) {
            ctx.fillStyle = '#ff0';
            ctx.fillRect(b.x, b.y, b.w, b.h);
        }

        function drawMeteor(m) {
            ctx.save();
            ctx.translate(m.x + m.w / 2, m.y + m.h / 2);
            ctx.rotate(m.rotation);

            ctx.fillStyle = '#7a7a7a';
            ctx.beginPath();
            ctx.arc(0, 0, m.w / 2, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = '#5a5a5a';
            for (let i = 0; i < 3; i++) {
                const angle = (i / 3) * Math.PI * 2;
                const dist = m.w / 4;
                ctx.beginPath();
                ctx.arc(Math.cos(angle) * dist, Math.sin(angle) * dist, m.w / 8, 0, Math.PI * 2);
                ctx.fill();
            }

            ctx.restore();
        }

        function update() {
            if (!gameActive) return;

            const dx = mouseX - (player.x + player.w / 2);
            const dy = mouseY - (player.y + player.h / 2);
            player.x += dx * player.speed;
            player.y += dy * player.speed;

            player.x = Math.max(0, Math.min(canvas.width - player.w, player.x));
            player.y = Math.max(Math.min(canvas.height - player.h, player.y), Math.min(canvas.height / 2 - player.h));

            if (mouseDown) {
                shootBullet();
            }

            bullets = bullets.filter(b => {
                b.y -= b.speed;
                return b.y > -b.h;
            });

            const now = Date.now();
            if (now - lastMeteorSpawn > meteorSpawnRate) {
                spawnMeteor();
                lastMeteorSpawn = now;
                meteorSpawnRate = Math.max(500, meteorSpawnRate - 5);
            }

            meteors = meteors.filter(m => {
                m.y += m.speed;
                m.rotation += m.rotSpeed;

                const playerCenterX = player.x + player.w / 2;
                const playerCenterY = player.y + player.h / 2;
                const meteorCenterX = m.x + m.w / 2;
                const meteorCenterY = m.y + m.h / 2;
                const distToPlayer = Math.sqrt(
                    Math.pow(playerCenterX - meteorCenterX, 2) +
                    Math.pow(playerCenterY - meteorCenterY, 2)
                );

                if (distToPlayer < m.w / 2 + player.w / 2) {
                    health -= 20;
                    document.getElementById('health').textContent = health;
                    const explosion = document.getElementById('explosion');
                    explosion.play();
                    if (health <= 0) {
                        gameOver();
                    }
                    return false;
                }

                if (m.y > canvas.height + m.h) {
                    health -= 10;
                    document.getElementById('health').textContent = health;
                    if (health <= 0) {
                        gameOver();
                    }
                    return false;
                }

                for (let i = bullets.length - 1; i >= 0; i--) {
                    const b = bullets[i];
                    const dx = (m.x + m.w / 2) - (b.x + b.w / 2);
                    const dy = (m.y + m.h / 2) - (b.y + b.h / 2);
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < m.w / 2 + b.h / 2) {
                        bullets.splice(i, 1);
                        score += 10;
                        document.getElementById('score').textContent = score;
                        return false;
                    }
                }

                return true;
            });
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            drawPlayer();
            bullets.forEach(drawBullet);
            meteors.forEach(drawMeteor);
        }

        function gameLoop() {
            update();
            draw();
            requestAnimationFrame(gameLoop);
        }

        function gameOver() {
            gameActive = false;
            document.getElementById('finalScore').textContent = score;
            document.getElementById('gameOver').style.display = 'block';
            const dead = document.getElementById('dead');
            dead.play()
        }

        function restartGame() {
            gameActive = true;
            score = 0;
            health = 100;
            bullets = [];
            meteors = [];
            meteorSpawnRate = 1000;
            player.x = canvas.width / 2 - 20;
            player.y = canvas.height - 80;
            document.getElementById('score').textContent = score;
            document.getElementById('health').textContent = health;
            document.getElementById('gameOver').style.display = 'none';
        }

        gameLoop();
    </script>
</body>

</html>
"""

@app.route('/game')
def game():
    return render_template_string(HTML_GAME)

@app.route('/simulation')
def simulate():
    return render_template_string(HTML_TEMPLATE)

@app.route('/about')
def about():
    return render_template_string(HTML_ABOUT)

@app.route('/')
def index():
    return render_template_string(HTML_WELCOME)

@app.route('/api/asteroids')
def get_asteroids():
    asteroids = list(ASTEROIDS.keys())
    return jsonify(asteroids)

@app.route('/api/locations')
def get_locations():
    return jsonify(LOCATIONS)

@app.route('/api/simulate', methods=['POST'])
def simulate_impact():
    data = request.json
    
    asteroid_name = data.get('asteroid')
    location_name = data.get('location')
    velocity = data.get('velocity')
    
    if asteroid_name not in ASTEROIDS:
        return jsonify({"error": "Invalid asteroid"}), 400
    
    if location_name not in LOCATIONS:
        return jsonify({"error": "Invalid location"}), 400
    
    asteroid = ASTEROIDS[asteroid_name]
    location = LOCATIONS[location_name]
    
    energy_mt = calculate_impact_energy(
        asteroid['diameter_km'],
        velocity,
        asteroid['density']
    )
    
    radius_20_psi = calculate_psi_radius(energy_mt, 20)
    radius_3_psi = calculate_psi_radius(energy_mt, 3)
    
    affected_severe = estimate_affected_population(radius_20_psi, location)
    affected_moderate = estimate_affected_population(radius_3_psi, location)
    
    result = {
        "asteroid": asteroid_name,
        "asteroid_info": {
            "diameter_km": asteroid['diameter_km'],
            "spectral_type": asteroid['spectral_type'],
            "density": asteroid['density']
        },
        "location": location_name,
        "coordinates": {
            "lat": location['lat'],
            "lon": location['lon']
        },
        "velocity_km_s": velocity,
        "energy_megatons": round(energy_mt, 2),
        "damage_zones": {
            "severe": {
                "psi": 20,
                "radius_km": round(radius_20_psi, 2),
                "description": "Total building collapse, near 100% casualties",
                "estimated_affected": affected_severe
            },
            "moderate": {
                "psi": 3,
                "radius_km": round(radius_3_psi, 2),
                "description": "Severe structural damage, glass shattering, ~50% casualties",
                "estimated_affected": affected_moderate
            }
        }
    }
    
    return jsonify(result)

if __name__ == '__main__':
    print("\nServer starting...")
    print("Open your browser: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)
