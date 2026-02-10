import os
import requests
from flask import Flask, render_template_string, send_from_directory

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

os.makedirs('static', exist_ok=True)
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
        select { padding: 10px; border-radius: 5px; border: 1px solid #ccc; width: 200px; font-size: 14px; }
        #map { height: 80vh; width: 100%; }

        .info.legend {
            background: rgba(255,255,255,0.95);
            padding: 12px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            line-height: 22px;
            font-size: 13px;
            border: 2px solid #001f3f;
        }
        .info.legend i {
            width: 20px;
            height: 20px;
            float: left;
            margin-right: 10px;
            border: 1px solid #999;
        }
    </style>
</head>
<body>

<div class="header">
    <h2 style="margin:0;">Análisis de Riesgo por Parroquia</h2>
</div>

<div class="controls">
    <select id="prov"><option value="">Provincia...</option></select>
    <select id="can" disabled><option value="">Cantón...</option></select>
    <select id="par" disabled><option value="">Parroquia...</option></select>
</div>

<div id="map"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([-1.83, -78.18], 7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

var geoLayer, riskData = {};

// COLORES (amarillo SOLO para 0)
function getColor(d) {
    return d === 0    ? '#FFEDA0' :
           d <= 0.2  ? '#FD8D3C' :
           d <= 0.4  ? '#FC4E2A' :
           d <= 0.6  ? '#E31A1C' :
           d <= 0.8  ? '#BD0026' :
                       '#800026';
}

// LEYENDA COINCIDENTE CON getColor()
var legend = L.control({position: 'topright'});
legend.onAdd = function () {
    var div = L.DomUtil.create('div', 'info legend');

    div.innerHTML =
        '<strong style="display:block; margin-bottom:8px; text-align:center; border-bottom:1px solid #ccc;">Nivel de Riesgos</strong>' +
        '<i style="background:#FFEDA0"></i> 0%<br>' +
        '<i style="background:#FD8D3C"></i> > 0%<br>' +
        '<i style="background:#FC4E2A"></i> ≤ 40%<br>' +
        '<i style="background:#E31A1C"></i> ≤ 60%<br>' +
        '<i style="background:#BD0026"></i> ≤ 80%<br>' +
        '<i style="background:#800026"></i> > 80%';

    return div;
};
legend.addTo(map);

Promise.all([
    fetch('/static/{{NOMBRE_JSON}}').then(r => r.json()),
    fetch('/static/{{NOMBRE_CSV}}').then(r => r.text())
]).then(([geojsonData, csvText]) => {

    csvText.split('\\n').slice(1).forEach(row => {
        var c = row.split(',');
        if (c.length >= 4) {
            riskData[c[0].trim().padStart(6,'0')] = parseFloat(c[3]);
        }
    });

    geoLayer = L.geoJson(geojsonData, {
        style: f => ({
            fillColor: getColor(riskData[f.properties.DPA_PARROQ] || 0),
            weight: 0.6,
            color: 'white',
            fillOpacity: 0.7
        }),
        onEachFeature: (f, l) => {
            var p = riskData[f.properties.DPA_PARROQ] || 0;
            l.bindPopup(
                '<b>' + f.properties.DPA_DESPAR + '</b><br>' +
                'Provincia: ' + f.properties.DPA_DESPRO + '<br>' +
                'Cantón: ' + f.properties.DPA_DESCAN + '<hr>' +
                'Riesgo: ' + (p*100).toFixed(2) + '%'
            );
        }
    }).addTo(map);
});
</script>
</body>
</html>
"""

html_maestro = html_maestro.replace("{{NOMBRE_JSON}}", NOMBRE_JSON).replace("{{NOMBRE_CSV}}", NOMBRE_CSV)

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string(html_maestro)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
