import os
import requests
from flask import Flask, render_template_string, send_from_directory

# CONFIGURACIÓN DE ARCHIVOS #
ID_JSON_DRIVE = '1u8uvcR8Mf5U3bXqbu8Qv2wiKJuhilCbJ'
ID_CSV_PREDICCIONES = '1oBLdLOrhf78O67jmmSOu_45UZg1LWtFK'
ID_CSV_CODIFICACION = '1SHE3Pv_os0bL-IqT3cEO7LMFbChOsDvK' 

NOMBRE_JSON = 'mapa_ecuador.json'
NOMBRE_CSV_PRED = 'predicciones.csv'
NOMBRE_CSV_MASTER = 'codificacion_2025.csv'

def descargar_de_drive(file_id, output_path):
    if os.path.exists(output_path):
        os.remove(output_path)
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
    except Exception as e:
        print(f"Error descargando {output_path}: {e}")

os.makedirs('static', exist_ok=True)
descargar_de_drive(ID_JSON_DRIVE, f'static/{NOMBRE_JSON}')
descargar_de_drive(ID_CSV_PREDICCIONES, f'static/{NOMBRE_CSV_PRED}')
descargar_de_drive(ID_CSV_CODIFICACION, f'static/{NOMBRE_CSV_MASTER}')

html_maestro = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Mapa de Riesgo Ecuador - Full Pro</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin:0; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:#f0f2f5; }
        .header { background:#001f3f; color:white; padding:15px; text-align:center; box-shadow:0 4px 10px rgba(0,0,0,0.3); }
        .controls {
            display:flex; flex-wrap:wrap; gap:12px; padding:15px; background:white;
            justify-content:center; border-bottom:2px solid #ddd; align-items:center;
        }
        select, input { padding:10px; border-radius:6px; border:1px solid #ccc; width:190px; font-size:14px; }
        button { padding:10px 20px; cursor:pointer; background:#001f3f; color:white; border:none; border-radius:6px; font-weight:bold; transition: 0.3s; }
        button:hover { background:#003366; transform: scale(1.05); }
        #map { height:calc(100vh - 145px); width:100%; }
        .info.legend { background:rgba(255,255,255,0.95); padding:12px; border-radius:8px; border:2px solid #001f3f; line-height:22px; font-weight:500; }
        .info.legend i { width:20px; height:20px; float:left; margin-right:10px; border:1px solid #999; }
    </style>
</head>
<body>

<div class="header"><h2 style="margin:0;">📍 Análisis de Riesgo por Parroquia (Ecuador 2025)</h2></div>

<div class="controls">
    <select id="prov"><option value="">Provincia...</option></select>
    <select id="can" disabled><option value="">Cantón...</option></select>
    <select id="par" disabled><option value="">Parroquia...</option></select>
    <input type="text" id="busqueda" placeholder="Ej: oyeturo (Molleturo)...">
    <button onclick="buscarInteligente()">Buscar</button>
    <button onclick="location.reload()" style="background:#666;">Reiniciar</button>
</div>

<div id="map"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([-1.83,-78.18],7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

var geoLayer, riskData = {}, masterData = [], rawGeoJSON;

// --- FUNCIÓN DE SIMILITUD (Levenshtein) ---
function similitud(s1, s2) {
    s1 = s1.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
    s2 = s2.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
    var costs = new Array();
    for (var i = 0; i <= s1.length; i++) {
        var lastValue = i;
        for (var j = 0; j <= s2.length; j++) {
            if (i == 0) costs[j] = j;
            else {
                if (j > 0) {
                    var newValue = costs[j - 1];
                    if (s1.charAt(i - 1) != s2.charAt(j - 1))
                        newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
                    costs[j - 1] = lastValue;
                    lastValue = newValue;
                }
            }
        }
        if (i > 0) costs[s2.length] = lastValue;
    }
    return costs[s2.length];
}

// Escala de Colores Original
function getColor(d){
    if (d === undefined || d === null) return '#E0E0E0';
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
    div.innerHTML = '<strong>Nivel de Riesgo</strong><br>'+
        '<i style="background:#FFEDA0"></i> 0%<br>'+
        '<i style="background:#FD8D3C"></i> 1% - 20%<br>'+
        '<i style="background:#FC4E2A"></i> 21% - 40%<br>'+
        '<i style="background:#E31A1C"></i> 41% - 60%<br>'+
        '<i style="background:#BD0026"></i> 61% - 80%<br>'+
        '<i style="background:#800026"></i> > 80%';
    return div;
};
legend.addTo(map);

async function init() {
    const [resGeo, resPred, resMaster] = await Promise.all([
        fetch('/static/{{NOMBRE_JSON}}'),
        fetch('/static/{{NOMBRE_CSV_PRED}}'),
        fetch('/static/{{NOMBRE_CSV_MASTER}}')
    ]);

    rawGeoJSON = await resGeo.json();
    const decoder = new TextDecoder('utf-8');
    
    // Procesar Predicciones
    const csvPred = decoder.decode(await resPred.arrayBuffer());
    csvPred.split('\\n').slice(1).forEach(r => {
        let c = r.split(',');
        if(c.length >= 4) riskData[c[0].trim().padStart(6,'0')] = parseFloat(c[3]);
    });

    // Procesar Master 2025
    const csvMaster = decoder.decode(await resMaster.arrayBuffer());
    csvMaster.split('\\n').slice(2).forEach(r => {
        let c = r.split(',');
        if(c.length >= 7) {
            masterData.push({
                prov: c[2].trim(), can: c[4].trim(),
                id: c[5].trim().padStart(6,'0'), nom: c[6].trim()
            });
        }
    });

    // Cargar Mapa
    geoLayer = L.geoJson(rawGeoJSON, {
        style: f => ({
            fillColor: getColor(riskData[f.properties.DPA_PARROQ.toString().padStart(6,'0')]),
            weight: 1, color: 'white', fillOpacity: 0.75
        }),
        onEachFeature: (f, l) => {
            let id = f.properties.DPA_PARROQ.toString().padStart(6,'0');
            let p = riskData[id];
            l.bindPopup(`
                <div style="font-size:14px;">
                    <b style="color:#001f3f; font-size:16px;">${f.properties.DPA_DESPAR}</b><br>
                    <b>Provincia:</b> ${f.properties.DPA_DESPRO}<br>
                    <b>Cantón:</b> ${f.properties.DPA_DESCAN}<hr>
                    <b style="font-size:15px;">Riesgo: ${p !== undefined ? (p*100).toFixed(2)+'%' : 'Sin datos'}</b>
                </div>
            `);
        }
    }).addTo(map);

    // --- LÓGICA DE SELECTORES Y ZOOMS ---
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
            
            // Zoom a la Provincia
            let featuresProv = rawGeoJSON.features.filter(f => f.properties.DPA_DESPRO === selProv.value);
            if(featuresProv.length > 0) map.fitBounds(L.geoJson(featuresProv).getBounds());
        }
    };

    selCan.onchange = () => {
        selPar.innerHTML = '<option value="">Parroquia...</option>';
        selPar.disabled = !selCan.value;
        if(selCan.value) {
            const pars = masterData.filter(m => m.prov === selProv.value && m.can === selCan.value);
            let unicas = {};
            pars.forEach(p => unicas[p.id] = p.nom);
            Object.keys(unicas).sort((a,b)=>unicas[a].localeCompare(unicas[b]))
                .forEach(id => selPar.add(new Option(unicas[id], id)));
            
            // Zoom al Cantón
            let featuresCan = rawGeoJSON.features.filter(f => f.properties.DPA_DESPRO === selProv.value && f.properties.DPA_DESCAN === selCan.value);
            if(featuresCan.length > 0) map.fitBounds(L.geoJson(featuresCan).getBounds());
        }
    };

    selPar.onchange = () => {
        geoLayer.eachLayer(l => {
            if(l.feature.properties.DPA_PARROQ.toString().padStart(6,'0') === selPar.value) {
                map.fitBounds(l.getBounds());
                l.openPopup();
            }
        });
    };
}

function buscarInteligente() {
    var entrada = document.getElementById('busqueda').value;
    if (!entrada) return;

    var mejorMatch = null;
    var menorDistancia = 999;

    masterData.forEach(p => {
        var d = similitud(entrada, p.nom);
        if (d < menorDistancia) {
            menorDistancia = d;
            mejorMatch = p;
        }
    });

    if (mejorMatch && menorDistancia < 5) {
        document.getElementById('prov').value = mejorMatch.prov;
        document.getElementById('prov').dispatchEvent(new Event('change'));
        setTimeout(() => {
            document.getElementById('can').value = mejorMatch.can;
            document.getElementById('can').dispatchEvent(new Event('change'));
            setTimeout(() => {
                document.getElementById('par').value = mejorMatch.id;
                document.getElementById('par').dispatchEvent(new Event('change'));
            }, 200);
        }, 200);
    } else {
        alert("No se encontró una parroquia similar.");
    }
}

init();
</script>
</body>
</html>
"""

html_maestro = html_maestro.replace("{{NOMBRE_JSON}}", NOMBRE_JSON) \
                           .replace("{{NOMBRE_CSV_PRED}}", NOMBRE_CSV_PRED) \
                           .replace("{{NOMBRE_CSV_MASTER}}", NOMBRE_CSV_MASTER)

app = Flask(__name__)
@app.route('/')
def home(): return render_template_string(html_maestro)

@app.route('/static/<path:filename>')
def serve_static(filename): return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
