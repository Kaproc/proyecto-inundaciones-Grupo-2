import os
import requests
from Flask import Flask, render_template_string, send_from_directory

# CONFIGURACIÓN DE ARCHIVOS #
ID_JSON_DRIVE = '1u8uvcR8Mf5U3bXqbu8Qv2wiKJuhilCbJ'
ID_CSV_DRIVE = '1oBLdLOrhf78O67jmmSOu_45UZg1LWtFK'

NOMBRE_JSON = 'ORGANIZACION TERRITORIAL DEL ESTADO PARROQUIAL (1).json'
NOMBRE_CSV = 'predicciones_modelo_final_con_id.csv'

def descargar_de_drive(file_id, output_path):
    if os.path.exists(output_path):
        return
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"Descargado: {output_path}")
    except Exception as e:
        print(f"Error en descarga: {e}")

# Crear carpeta static y bajar archivos
os.makedirs('static', True)
descargar_de_drive(ID_JSON_DRIVE, f'static/{NOMBRE_JSON}')
descargar_de_drive(ID_CSV_DRIVE, f'static/{NOMBRE_CSV}')

html_maestro = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Mapa de Riesgo Ecuador</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin: 0; font-family: 'Segoe UI', Tahoma, sans-serif; background: #f0f2f5; }
        .header { background: #001f3f; color: white; padding: 10px; text-align: center; }
        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            padding: 15px;
            background: white;
            justify-content: center;
            align-items: center;
            border-bottom: 2px solid #ddd;
        }
        select, input { padding: 10px; border-radius: 5px; border: 1px solid #ccc; width: 200px; font-size: 14px; }
        #map { height: 80vh; width: 100%; position: relative; }
        
        /* LEYENDA AGRANDADA */
        .info.legend {
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            line-height: 24px;
            color: #333;
            font-size: 14px;
            border: 2px solid #001f3f;
            min-width: 140px;
        }
        .info.legend i {
            width: 22px;
            height: 22px;
            float: left;
            margin-right: 10px;
            opacity: 0.9;
            border: 1px solid #999;
        }
    </style>
</head>
<body>
    <div class="header"><h2 style="margin:0;">Análisis de Riesgo por Parroquia</h2></div>

    <div class="controls">
        <select id="prov"><option value="">Provincia...</option></select>
        <select id="can" disabled><option value="">Cantón...</option></select>
        <select id="par" disabled><option value="">Parroquia...</option></select>
        <button onclick="location.reload()" style="padding: 10px; cursor: pointer; border-radius: 5px; background: #f8f9fa; border: 1px solid #ddd;">Reiniciar</button>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([-1.83, -78.18], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        var geoLayer, riskData = {};

        function getColor(d) {
            return d > 0.8  ? '#800026' : 
                   d > 0.6  ? '#BD0026' : 
                   d > 0.4  ? '#E31A1C' : 
                   d > 0.2  ? '#FC4E2A' : 
                   d > 0.01 ? '#FD8D3C' : 
                              '#FFEDA0';
        }

        var legend = L.control({position: 'topright'});
        legend.onAdd = function (map) {
            var div = L.DomUtil.create('div', 'info legend');
            var grades = [0, 0.01, 0.2, 0.4, 0.6, 0.8];
            
            div.innerHTML = '<strong style="display:block; margin-bottom:8px; text-align:center; border-bottom:1px solid #ccc;">Nivel de Riesgo</strong>';

            for (var i = 0; i < grades.length; i++) {
                div.innerHTML +=
                    '<i style="background:' + getColor(grades[i] + 0.001) + '"></i> ' +
                    (grades[i] * 100).toFixed(0) + '%' + (grades[i + 1] ? '&ndash;' + (grades[i + 1] * 100).toFixed(0) + '%' + '<br>' : '+');
            }
            return div;
        };
        legend.addTo(map);

        const urlJson = encodeURI('/static/{{NOMBRE_JSON}}');
        const urlCsv = encodeURI('/static/{{NOMBRE_CSV}}');

        Promise.all([
            fetch(urlJson).then(r => r.json()),
            fetch(urlCsv).then(r => r.text())
        ]).then(([geojsonData, csvText]) => {

            csvText.split('\\n').slice(1).forEach(row => {
                var cols = row.split(',');
                if(cols.length >= 4) {
                    var id = cols[0].trim().padStart(6, '0');
                    riskData[id] = parseFloat(cols[3]);
                }
            });

            geoLayer = L.geoJson(geojsonData, {
                style: (f) => ({
                    fillColor: getColor(riskData[f.properties.DPA_PARROQ] || 0),
                    weight: 0.6, opacity: 1, color: 'white', fillOpacity: 0.7
                }),
                onEachFeature: (f, l) => {
                    var p = riskData[f.properties.DPA

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
