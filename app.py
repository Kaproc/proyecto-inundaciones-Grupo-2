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

# Crear carpeta static y bajar archivos
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
        select, input { padding: 10px; border-radius: 5px; border: 1px solid #ccc; width: 200px; font-size: 14px; }
        #map { height: 80vh; width: 100%; position: relative; }
        
        .info.legend {
            background: rgba(255, 255, 255, 0.95);
            padding: 12px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            line-height: 22px;
            color: #333;
            font-size: 13px;
            border: 2px solid #001f3f;
        }
        .info.legend i {
            width: 20px;
            height: 20px;
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
        <button onclick="location.reload()" style="padding: 10px; cursor: pointer; background: #f8f9fa; border: 1px solid #ddd; border-radius: 5px;">Reiniciar Mapa</button>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([-1.83, -78.18], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        var geoLayer, riskData = {};

        // CORRECCIÓN: Lógica de colores sincronizada con la leyenda
        function getColor(d) {
            return d > 0.8  ? '#800026' : 
                   d > 0.6  ? '#BD0026' : 
                   d > 0.4  ? '#E31A1C' : 
                   d > 0.2  ? '#FC4E2A' : 
                   d > 0.05 ? '#FD8D3C' : 
                              '#FFEDA0';
        }

        var legend = L.control({position: 'topright'});
        legend.onAdd = function (map) {
            var div = L.DomUtil.create('div', 'info legend'),
                grades = [0, 0.05, 0.2, 0.4, 0.6, 0.8],
                labels = ['<strong style="display:block; margin-bottom:8px; text-align:center; border-bottom:1px solid #ccc;">Nivel de Riesgo</strong>'];

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
                    var p = riskData[f.properties.DPA_PARROQ] || 0;
                    var contenido = '<div style="font-size:13px;">' +
                        '<b style="color:#001f3f;">' + f.properties.DPA_DESPAR + '</b><br>' +
                        '<b>Provincia:</b> ' + f.properties.DPA_DESPRO + '<br>' +
                        '<b>Cantón:</b> ' + f.properties.DPA_DESCAN + '<br>' +
                        '<hr style="border:0; border-top:1px solid #eee;">' +
                        '<b>Riesgo:</b> ' + (p * 100).toFixed(2) + '%' +
                        '</div>';
                    l.bindPopup(contenido);
                }
            }).addTo(map);

            const selProv = document.getElementById('prov');
            const selCan = document.getElementById('can');
            const selPar = document.getElementById('par');

            const provincias = [...new Set(geojsonData.features.map(f => f.properties.DPA_DESPRO))].sort();
            provincias.forEach(p => selProv.add(new Option(p, p)));

            selProv.onchange = () => {
                selCan.innerHTML = '<option value="">Cantón...</option>';
                selPar.innerHTML = '<option value="">Parroquia...</option>';
                selCan.disabled = !selProv.value;
                selPar.disabled = true;
                if (selProv.value) {
                    const filtered = geojsonData.features.filter(f => f.properties.DPA_DESPRO === selProv.value);
                    const cantones = [...new Set(filtered.map(f => f.properties.DPA_DESCAN))].sort();
                    cantones.forEach(c => selCan.add(new Option(c, c)));
                    map.fitBounds(L.geoJson(filtered).getBounds());
                }
            };

            selCan.onchange = () => {
                selPar.innerHTML = '<option value="">Parroquia...</option>';
                selPar.disabled = !selCan.value;
                if (selCan.value) {
                    const filtered = geojsonData.features.filter(f =>
                        f.properties.DPA_DESPRO === selProv.value &&
                        f.properties.DPA_DESCAN === selCan.value
                    );
                    filtered.sort((a,b) => a.properties.DPA_DESPAR.localeCompare(b.properties.DPA_DESPAR))
                            .forEach(f => selPar.add(new Option(f.properties.DPA_DESPAR, f.properties.DPA_PARROQ)));
                    map.fitBounds(L.geoJson(filtered).getBounds());
                }
            };

            selPar.onchange = () => {
                geoLayer.eachLayer(l => {
                    if(l.feature.properties.DPA_PARROQ === selPar.value) {
                        map.fitBounds(l.getBounds());
                        l.openPopup();
                    }
                });
            };
        });
    </script>
</body>
</html>
"""

# Reemplazo de variables en el HTML
html_maestro = html_maestro.replace("{{NOMBRE_JSON}}", NOMBRE_JSON).replace("{{NOMBRE_CSV}}", NOMBRE_CSV)

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string(html_maestro)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
