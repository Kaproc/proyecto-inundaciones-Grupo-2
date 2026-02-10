import os
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

# CONFIGURACIÓN DE ARCHIVOS (MANTENIENDO NOMBRES ORIGINALES)
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

# Crear carpeta static si no existe
if not os.path.exists('static'):
    os.makedirs('static')

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
        body { margin: 0; font-family: 'Segoe UI', Tahoma, sans-serif; background: #f8f9fa; }
        .header { background: #001f3f; color: white; padding: 10px; text-align: center; border-bottom: 3px solid #ffcc00; }
        #map { height: 90vh; width: 100%; }
        
        /* LEYENDA MEJORADA */
        .info.legend {
            background: white; padding: 12px; border-radius: 5px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2); line-height: 20px; color: #333;
        }
        .info.legend i {
            width: 20px; height: 20px; float: left; margin-right: 10px;
            opacity: 0.8; border: 1px solid #ccc;
        }
    </style>
</head>
<body>
    <div class="header"><h2 style="margin:0;">Análisis de Riesgo por Parroquia - Ecuador</h2></div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([-1.83, -78.18], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        var riskData = {};

        // NUEVA PALETA DE COLORES: 0% es Gris Neutro para que no se vea "amarillo raro"
        function getColor(d) {
            if (d <= 0) return '#f0f0f0'; // Gris casi blanco para 0%
            return d > 0.8  ? '#800026' : 
                   d > 0.6  ? '#BD0026' : 
                   d > 0.4  ? '#E31A1C' : 
                   d > 0.2  ? '#FC4E2A' : 
                   d > 0.01 ? '#feb24c' : // Naranja claro para riesgo bajo
                              '#ffeda0';  // Amarillo solo si es > 0 y < 0.01
        }

        // Cargamos los archivos usando los nombres originales
        const urlJson = '/static/' + encodeURIComponent('{{NOMBRE_JSON}}');
        const urlCsv = '/static/' + encodeURIComponent('{{NOMBRE_CSV}}');

        Promise.all([
            fetch(urlJson).then(r => r.json()),
            fetch(urlCsv).then(r => r.text())
        ]).then(([geojsonData, csvText]) => {

            // Procesar el CSV
            const rows = csvText.split('\\n');
            rows.forEach((row, index) => {
                if (index === 0 || row.trim() === "") return;
                var cols = row.split(',');
                if(cols.length >= 4) {
                    // Limpiar ID (quitar comillas y asegurar 6 dígitos)
                    var id = cols[0].replace(/"/g, '').trim().padStart(6, '0');
                    var valor = parseFloat(cols[3]);
                    riskData[id] = valor;
                }
            });

            // Dibujar el mapa
            L.geoJson(geojsonData, {
                style: function(f) {
                    var r = riskData[f.properties.DPA_PARROQ] || 0;
                    return {
                        fillColor: getColor(r),
                        weight: 0.5, opacity: 1, color: '#666', fillOpacity: 0.8
                    };
                },
                onEachFeature: function(f, l) {
                    var r = riskData[f.properties.DPA_PARROQ] || 0;
                    var nom = f.properties.DPA_DESPAR || "Desconocida";
                    l.bindPopup("<b>Parroquia:</b> " + nom + "<br><b>Riesgo:</b> " + (r * 100).toFixed(2) + "%");
                    
                    l.on({
                        mouseover: function(e) { e.target.setStyle({ weight: 2, color: '#000', fillOpacity: 1 }); },
                        mouseout: function(e) { e.target.setStyle({ weight: 0.5, color: '#666', fillOpacity: 0.8 }); }
                    });
                }
            }).addTo(map);

            // Añadir Leyenda
            var legend = L.control({position: 'bottomright'});
            legend.onAdd = function (map) {
                var div = L.DomUtil.create('div', 'info legend');
                var grades = [0, 0.01, 0.2, 0.4, 0.6, 0.8];
                div.innerHTML = '<b>Nivel de Riesgo</b><br>';
                for (var i = 0; i < grades.length; i++) {
                    div.innerHTML +=
                        '<i style="background:' + getColor(grades[i] + 0.001) + '"></i> ' +
                        (grades[i] * 100).toFixed(0) + '%' + (grades[i + 1] ? '&ndash;' + (grades[i + 1] * 100).toFixed(0) + '%<br>' : '+');
                }
                return div;
            };
            legend.addTo(map);

        }).catch(err => console.error("Error cargando datos:", err));
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_maestro, NOMBRE_JSON=NOMBRE_JSON, NOMBRE_CSV=NOMBRE_CSV)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
