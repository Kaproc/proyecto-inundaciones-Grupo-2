import os
import requests
from flask import Flask, render_template_string, send_from_directory

# CONFIGURACIÓN DE ARCHIVOS (IDs verificados) #
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
    <title>Mapa de Riesgo Ecuador - Sistema Completo</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin:0; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:#f0f2f5; }
        .header { background:#001f3f; color:white; padding:15px; text-align:center; box-shadow:0 4px 10px rgba(0,0,0,0.3); }
        .controls {
            display:flex; flex-wrap:wrap; gap:12px; padding:15px; background:white;
            justify-content:center; border-bottom:2px solid #ddd; align-items:center;
        }
        select, input { padding:10px; border-radius:6px; border:1px solid #ccc; width:190px; font-size:14px; }
        button { padding:10px 20px; cursor:pointer; background:#001f3f; color:white; border:none; border-radius:6px; font-weight:bold; }
        button:hover { background:#003366; }
        #map { height:calc(100vh - 145px); width:100%; background: #aad3df; }
        .info.legend { background:rgba(255,255,255,0.95); padding:12px; border-radius:8px; border:2px solid #001f3f; line-height:22px; }
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

// --- ALGORITMO LEVENSHTEIN RECUPERADO ---
function similitud(s1, s2) {
    s1 = s1.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").trim();
    s2 = s2.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").trim();
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

// Escala de Colores Original Recuperada
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
        '<i style="background:#800026"></i> > 80%<br>'+
        '<i style="background:#E0E0E0"></i> Sin Datos';
    return div;
};
legend.addTo(map);

// Función para limpiar textos de CSV (quita cometas y espacios)
function limpiarCSV(t) {
    return t ? t.replace(/[\\r\\n"]+/g, '').trim() : "";
}

async function init() {
    const [resGeo, resPred, resMaster] = await Promise.all([
        fetch('/static/{{NOMBRE_JSON}}'),
        fetch('/static/{{NOMBRE_CSV_PRED}}'),
        fetch('/static/{{NOMBRE_CSV_MASTER}}')
    ]);

    rawGeoJSON = await resGeo.json();
    const decoder = new TextDecoder('utf-8');
    
    // 1. Cargar Predicciones (ID, true, pred, prob)
    const csvPred = decoder.decode(await resPred.arrayBuffer());
    csvPred.split('\\n').slice(1).forEach(r => {
        let c = r.split(',');
        if(c.length >= 4) {
            let id = c[0].trim().padStart(6,'0');
            riskData[id] = parseFloat(c[3]);
        }
    });

    // 2. Cargar Master 2025 (Evita duplicados y limpia símbolos)
    const csvMaster = decoder.decode(await resMaster.arrayBuffer());
    let idsVistos = new Set();
    csvMaster.split('\\n').slice(2).forEach(r => {
        let c = r.split(',');
        if(c.length >= 7) {
            let id = c[5].trim().padStart(6,'0');
            if(!idsVistos.has(id)) {
                masterData.push({
                    prov: limpiarCSV(c[2]), 
                    can: limpiarCSV(c[4]),
                    id: id, 
                    nom: limpiarCSV(c[6])
                });
                idsVistos.add(id);
            }
        }
    });

    // 3. Crear Capa de Mapa con Popups Completos
    geoLayer = L.geoJson(rawGeoJSON, {
        style: f => {
            let id = f.properties.DPA_PARROQ.toString().padStart(6,'0');
            return {
                fillColor: getColor(riskData[id]),
                weight: 1, color: 'white', fillOpacity: 0.75
            };
        },
        onEachFeature: (f, l) => {
            let id = f.properties.DPA_PARROQ.toString().padStart(6,'0');
            let prob = riskData[id];
            
            // Buscar info extra en el Master si el GeoJSON no la tiene
            let infoExtra = masterData.find(m => m.id === id) || { prov: f.properties.DPA_DESPRO, can: f.properties.DPA_DESCAN };

            l.bindPopup(`
                <div style="font-size:14px; min-width:150px;">
                    <b style="color:#001f3f; font-size:16px;">${f.properties.DPA_DESPAR}</b><br>
                    <b>Provincia:</b> ${infoExtra.prov || "N/A"}<br>
                    <b>Cantón:</b> ${infoExtra.can || "N/A"}<hr style="margin:8px 0;">
                    <b style="font-size:15px;">Prob. Riesgo: ${prob !== undefined ? (prob*100).toFixed(2)+'%' : '<span style="color:gray;">Sin datos</span>'}</b>
                </div>
            `);
        }
    }).addTo(map);

    // --- LÓGICA DE SELECTORES Y ZOOMS ---
    const selProv = document.getElementById('prov');
    const selCan = document.getElementById('can');
    const selPar = document.getElementById('par');

    const provincias = [...new Set(masterData.map(m => m.prov))].sort();
    provincias.forEach(p => { if(p) selProv.add(new Option(p, p)) });

    selProv.onchange = () => {
        selCan.innerHTML = '<option value="">Cantón...</option>';
        selPar.innerHTML = '<option value="">Parroquia...</option>';
        selCan.disabled = !selProv.value;
        if(selProv.value) {
            const cantones = [...new Set(masterData.filter(m => m.prov === selProv.value).map(m => m.can))].sort();
            cantones.forEach(c => selCan.add(new Option(c, c)));
            
            // Zoom a la Provincia
            let bounds = [];
            geoLayer.eachLayer(l => {
                if(l.feature.properties.DPA_DESPRO === selProv.value) bounds.push(l.getBounds());
            });
            if(bounds.length > 0) map.fitBounds(L.featureGroup(bounds.map(b => L.rectangle(b))).getBounds());
        }
    };

    selCan.onchange = () => {
        selPar.innerHTML = '<option value="">Parroquia...</option>';
        selPar.disabled = !selCan.value;
        if(selCan.value) {
            const pars = masterData.filter(m => m.prov === selProv.value && m.can === selCan.value);
            pars.sort((a,b)=>a.nom.localeCompare(b.nom)).forEach(p => selPar.add(new Option(p.nom, p.id)));
            
            // Zoom al Cantón
            let bounds = [];
            geoLayer.eachLayer(l => {
                if(l.feature.properties.DPA_DESCAN === selCan.value) bounds.push(l.getBounds());
            });
            if(bounds.length > 0) map.fitBounds(L.featureGroup(bounds.map(b => L.rectangle(b))).getBounds());
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

// BÚSQUEDA INTELIGENTE CON LEVENSHTEIN
function buscarInteligente() {
    var entrada = document.getElementById('busqueda').value;
    if (!entrada || entrada.length < 3) return;

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
            }, 300);
        }, 300);
    } else {
        alert("No se encontró una parroquia similar. Intenta ser más específico.");
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
