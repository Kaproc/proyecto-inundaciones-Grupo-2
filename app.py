import os
import requests
from flask import Flask, render_template_string, send_from_directory

# CONFIGURACIÓN DE ARCHIVOS #
ID_JSON_DRIVE = '1u8uvcR8Mf5U3bXqbu8Qv2wiKJuhilCbJ'
ID_CSV_PREDICCIONES = '1oBLdLOrhf78O67jmmSOu_45UZg1LWtFK'
ID_CSV_CODIFICACION = '1SHE3Pv_os0bL-IqT3cEO7LMFbChOsDvK' 

NOMBRE_JSON = 'ORGANIZACION TERRITORIAL DEL ESTADO PARROQUIAL (1).json'
NOMBRE_CSV_PRED = 'predicciones_modelo_final_con_id.csv'
NOMBRE_CSV_MASTER = 'codificacion_2025.csv'

def descargar_de_drive(file_id, output_path):
    if os.path.exists(output_path):
        return
    # Nota: Si es un Google Sheet, se descarga como CSV
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
    except Exception as e:
        print(f"Error descargando {output_path}: {e}")

# Preparar entorno
os.makedirs('static', exist_ok=True)
descargar_de_drive(ID_JSON_DRIVE, f'static/{NOMBRE_JSON}')
descargar_de_drive(ID_CSV_PREDICCIONES, f'static/{NOMBRE_CSV_PRED}')
descargar_de_drive(ID_CSV_CODIFICACION, f'static/{NOMBRE_CSV_MASTER}')

html_maestro = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Mapa de Riesgo Ecuador 2025</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin:0; font-family:Segoe UI,Tahoma,sans-serif; background:#f0f2f5; }
        .header { background:#001f3f; color:white; padding:10px; text-align:center; }
        .controls {
            display:flex; flex-wrap:wrap; gap:15px; padding:15px; background:white;
            justify-content:center; border-bottom:2px solid #ddd; align-items:center;
        }
        select, input { padding:10px; border-radius:5px; border:1px solid #ccc; width:200px; }
        button { padding:10px 15px; cursor:pointer; background:#001f3f; color:white; border:none; border-radius:5px; }
        #map { height:80vh; }
        .info.legend { background:rgba(255,255,255,0.9); padding:12px; border-radius:8px; line-height:22px; border:2px solid #001f3f; }
        .info.legend i { width:18px; height:18px; float:left; margin-right:8px; opacity:0.8; border:1px solid #999; }
    </style>
</head>
<body>

<div class="header">
    <h2 style="margin:0;">Análisis de Riesgo por Parroquia - Actualizado 2025</h2>
</div>

<div class="controls">
    <select id="prov"><option value="">Provincia...</option></select>
    <select id="can" disabled><option value="">Cantón...</option></select>
    <select id="par" disabled><option value="">Parroquia...</option></select>
    <input type="text" id="busqueda" placeholder="Buscar parroquia...">
    <button onclick="buscarInteligente()">Buscar</button>
    <button onclick="location.reload()" style="background:#666;">Reiniciar</button>
</div>

<div id="map"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([-1.83,-78.18],7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

var geoLayer, riskData = {}, masterData = [];

function getColor(d){
    if (d === undefined) return '#e0e0e0'; 
    return d === 0   ? '#FFEDA0' :
           d <= 0.2  ? '#FD8D3C' :
           d <= 0.4  ? '#FC4E2A' :
           d <= 0.6  ? '#E31A1C' :
           d <= 0.8  ? '#BD0026' :
                       '#800026';
}

var legend = L.control({position:'topright'});
legend.onAdd = function(){
    var div = L.DomUtil.create('div','info legend');
    div.innerHTML = '<strong>Probabilidad</strong><br>' +
        '<i style="background:#FFEDA0"></i> 0%<br>' +
        '<i style="background:#FD8D3C"></i> ≤ 20%<br>' +
        '<i style="background:#FC4E2A"></i> ≤ 40%<br>' +
        '<i style="background:#E31A1C"></i> ≤ 60%<br>' +
        '<i style="background:#BD0026"></i> ≤ 80%<br>' +
        '<i style="background:#800026"></i> > 80%';
    return div;
};
legend.addTo(map);

Promise.all([
    fetch('/static/{{NOMBRE_JSON}}').then(r=>r.json()),
    fetch('/static/{{NOMBRE_CSV_PRED}}').then(r=>r.text()),
    fetch('/static/{{NOMBRE_CSV_MASTER}}').then(r=>r.text())
]).then(([geojsonData, csvPred, csvMaster]) => {

    // 1. Cargar Predicciones
    csvPred.split('\\n').slice(1).forEach(r => {
        let c = r.split(',');
        if(c.length >= 4) riskData[c[0].trim().padStart(6,'0')] = parseFloat(c[3]);
    });

    // 2. Cargar Codificación 2025 (Skip 2 rows: empty and header)
    csvMaster.split('\\n').slice(2).forEach(r => {
        let c = r.split(',');
        if(c.length >= 7) {
            masterData.push({
                prov: c[2].trim(),
                can: c[4].trim(),
                idPar: c[5].trim().padStart(6,'0'),
                nomPar: c[6].trim()
            });
        }
    });

    // 3. Crear Capa GeoJSON
    geoLayer = L.geoJson(geojsonData, {
        style: f => ({
            fillColor: getColor(riskData[f.properties.DPA_PARROQ.padStart(6,'0')]),
            weight: 0.6, color: 'white', fillOpacity: 0.7
        }),
        onEachFeature: (f, l) => {
            let id = f.properties.DPA_PARROQ.padStart(6,'0');
            let prob = riskData[id];
            l.bindPopup('<b>'+f.properties.DPA_DESPAR+'</b><br>Riesgo: ' + (prob ? (prob*100).toFixed(2)+'%' : 'Sin datos'));
        }
    }).addTo(map);

    // 4. Configurar Selectores
    const selProv = document.getElementById('prov');
    const selCan = document.getElementById('can');
    const selPar = document.getElementById('par');

    const provincias = [...new Set(masterData.map(m => m.prov))].sort();
    provincias.forEach(p => selProv.add(new Option(p, p)));

    selProv.onchange = () => {
        selCan.innerHTML = '<option value="">Cantón...</option>';
        selPar.innerHTML = '<option value="">Parroquia...</option>';
        selCan.disabled = !selProv.value;
        if(selProv.value) {
            const cantones = [...new Set(masterData.filter(m => m.prov === selProv.value).map(m => m.can))].sort();
            cantones.forEach(c => selCan.add(new Option(c, c)));
        }
    };

    selCan.onchange = () => {
        selPar.innerHTML = '<option value="">Parroquia...</option>';
        selPar.disabled = !selCan.value;
        if(selCan.value) {
            const pars = masterData.filter(m => m.prov === selProv.value && m.can === selCan.value);
            // Evitar duplicados por sectores urbanos
            let unicas = {};
            pars.forEach(p => unicas[p.idPar] = p.nomPar);
            Object.keys(unicas).sort((a,b)=>unicas[a].localeCompare(unicas[b]))
                .forEach(id => selPar.add(new Option(unicas[id], id)));
        }
    };

    selPar.onchange = () => {
        let hallado = false;
        geoLayer.eachLayer(l => {
            if(l.feature.properties.DPA_PARROQ.padStart(6,'0') === selPar.value) {
                map.fitBounds(l.getBounds());
                l.openPopup();
                hallado = true;
            }
        });
        if(!hallado) alert("Parroquia oficial encontrada, pero no tiene geometría en el mapa actual.");
    };
});

function buscarInteligente() {
    let busq = document.getElementById('busqueda').value.toLowerCase();
    if(!busq) return;
    let match = masterData.find(m => m.nomPar.toLowerCase().includes(busq));
    if(match) {
        document.getElementById('prov').value = match.prov;
        document.getElementById('prov').dispatchEvent(new Event('change'));
        setTimeout(() => {
            document.getElementById('can').value = match.can;
            document.getElementById('can').dispatchEvent(new Event('change'));
            setTimeout(() => {
                document.getElementById('par').value = match.idPar;
                document.getElementById('par').dispatchEvent(new Event('change'));
            }, 100);
        }, 100);
    }
}
</script>
</body>
</html>
"""

# Inyectar nombres de archivos en el HTML
html_maestro = html_maestro.replace("{{NOMBRE_JSON}}", NOMBRE_JSON) \
                           .replace("{{NOMBRE_CSV_PRED}}", NOMBRE_CSV_PRED) \
                           .replace("{{NOMBRE_CSV_MASTER}}", NOMBRE_CSV_MASTER)

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string(html_maestro)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
