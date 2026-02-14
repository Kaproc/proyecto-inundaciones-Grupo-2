import os
import requests
from flask import Flask, render_template_string, send_from_directory

ID_JSON_DRIVE = '1u8uvcR8Mf5U3bXqbu8Qv2wiKJuhilCbJ'
ID_CSV_DRIVE = '1CMFX_z2xlSvsTeRgjYtP2W4hZbF7Nixk' 

NOMBRE_JSON = 'ORGANIZACION TERRITORIAL DEL ESTADO PARROQUIAL (1).json'
NOMBRE_CSV = 'predicciones_nacional_completo.csv'

def descargar_de_drive(file_id, output_path):
    if os.path.exists(output_path):
        return
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
    except Exception as e:
        print(f"Error: {e}")

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
body { margin:0; font-family:Segoe UI,Tahoma,sans-serif; background:#f0f2f5; }
.header { background:#001f3f; color:white; padding:10px; text-align:center; }
.controls {
    display:flex; flex-wrap:wrap; gap:15px; padding:15px; background:white;
    justify-content:center; border-bottom:2px solid #ddd; align-items:center;
}
select, input { padding:10px; border-radius:5px; border:1px solid #ccc; width:200px; }
button { padding:10px 15px; cursor:pointer; background:#001f3f; color:white; border:none; border-radius:5px; }
button:hover { background:#003366; }
#map { height:80vh; }

.info.legend {
    background:rgba(255,255,255,0.95);
    padding:12px;
    border-radius:8px;
    line-height:22px;
    border:2px solid #001f3f;
    box-shadow: 0 0 10px rgba(0,0,0,0.2);
}
.info.legend i {
    width:20px; height:20px;
    float:left; margin-right:8px;
    border:1px solid #999;
}
/* Estilo para el tooltip (Hover) */
.custom-tooltip {
    background: white;
    border: 1px solid #001f3f;
    color: #001f3f;
    font-weight: bold;
    font-size: 12px;
}
</style>
</head>
<body>

<div class="header">
<h2 style="margin:0;">Análisis de Riesgo de Inundación (SAT-Ecuador)</h2>
</div>

<div class="controls">
    <select id="prov"><option value="">Provincia...</option></select>
    <select id="can" disabled><option value="">Cantón...</option></select>
    <select id="par" disabled><option value="">Parroquia...</option></select>
    <input type="text" id="busqueda" placeholder="Buscar parroquia (ej: oyeturo)...">
    <button onclick="buscarInteligente()">Buscar</button>
    <button onclick="location.reload()" style="background:#666;">Reiniciar</button>
</div>

<div id="map"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([-1.83,-78.18],7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

var geoLayer, riskData = {}, parroquiasLista = [];

function getColor(d){
    return d === 0    ? '#FFEDA0' :
           d <= 0.2  ? '#FD8D3C' :
           d <= 0.4  ? '#FC4E2A' :
           d <= 0.6  ? '#E31A1C' :
           d <= 0.8  ? '#BD0026' :
                        '#800026';
}

function getRiskCategory(d) {
    if (d === 0) return "BAJO (Seguro)";
    if (d <= 0.4) return "MEDIO";
    if (d <= 0.7) return "ALTO";
    return "CRÍTICO";
}

var legend = L.control({position:'topright'});
legend.onAdd = function(){
    var div = L.DomUtil.create('div','info legend');
    div.innerHTML =
        '<strong style="display:block;text-align:center;margin-bottom:6px;">Nivel de Riesgo</strong>'+
        '<i style="background:#FFEDA0"></i> 0% (Bajo)<br>'+
        '<i style="background:#FD8D3C"></i> > 0%<br>'+
        '<i style="background:#FC4E2A"></i> ≤ 40% (Medio)<br>'+
        '<i style="background:#E31A1C"></i> ≤ 60%<br>'+
        '<i style="background:#BD0026"></i> ≤ 80% (Alto)<br>'+
        '<i style="background:#800026"></i> > 80% (Crítico)';
    return div;
};
legend.addTo(map);

function similitud(s1, s2) {
    s1 = s1.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    s2 = s2.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
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

function buscarInteligente() {
    var entrada = document.getElementById('busqueda').value;
    if (!entrada) return;
    var mejorCoincidencia = null; var menorDistancia = 999;
    parroquiasLista.forEach(p => {
        var d = similitud(entrada, p.nombre);
        if (d < menorDistancia) { menorDistancia = d; mejorCoincidencia = p; }
    });
    if (mejorCoincidencia && menorDistancia < 5) {
        geoLayer.eachLayer(l => {
            if(l.feature.properties.DPA_PARROQ === mejorCoincidencia.id) {
                map.fitBounds(l.getBounds());
                l.fire('click'); // Simular clic para abrir popup
            }
        });
    } else { alert("No se encontró una parroquia similar."); }
}

Promise.all([
    fetch('/static/{{NOMBRE_JSON}}').then(r=>r.json()),
    fetch('/static/{{NOMBRE_CSV}}').then(r=>r.text())
]).then(([geojsonData,csvText])=>{

    csvText.split('\\n').slice(1).forEach(r=>{
        let c=r.split(',');
        if(c.length>=3){
            riskData[c[0].trim().padStart(6,'0')] = parseFloat(c[2]); 
        }
    });

    geoLayer = L.geoJson(geojsonData,{
        style:f=>({
            fillColor:getColor(riskData[f.properties.DPA_PARROQ]||0),
            weight:0.6,
            color:'white',
            fillOpacity:0.7
        }),
        onEachFeature:(f,l)=>{
            let p=riskData[f.properties.DPA_PARROQ]||0;
            let cat = getRiskCategory(p);

            // Guardar para buscador
            parroquiasLista.push({ nombre: f.properties.DPA_DESPAR, id: f.properties.DPA_PARROQ });

            // --- 1. POPUP (CLIC) ---
            // Cumple Req: Categoría y Valor
            l.bindPopup(
                '<div style="text-align:center;">'+
                '<b style="font-size:14px; color:#001f3f;">'+f.properties.DPA_DESPAR+'</b><br>'+
                '<span style="color:#666;">'+f.properties.DPA_DESCAN+', '+f.properties.DPA_DESPRO+'</span><hr>'+
                '<b>Riesgo: </b>'+cat+'<br>'+
                '<b>Probabilidad: </b>'+(p*100).toFixed(1)+'%'+
                '</div>'
            );

            // --- 2. HOVER (PASAR EL MOUSE) ---
            // Cumple Req: Mostrar Nombre, Cantón, Provincia al pasar cursor
            l.bindTooltip(
                '<b>'+f.properties.DPA_DESPAR+'</b><br>'+f.properties.DPA_DESCAN,
                {className: 'custom-tooltip', sticky: true, direction: 'top'}
            );

            // Efecto Visual al Hover (Resaltar borde)
            l.on({
                mouseover: function(e) {
                    var layer = e.target;
                    layer.setStyle({
                        weight: 3,
                        color: '#333',
                        fillOpacity: 0.9
                    });
                    layer.bringToFront(); // Traer al frente para que se vea el borde
                },
                mouseout: function(e) {
                    geoLayer.resetStyle(e.target);
                },
                click: function(e) {
                    map.fitBounds(e.target.getBounds());
                }
            });
        }
    }).addTo(map);

    // Lógica de Selectores (Igual que antes)
    const selProv=document.getElementById('prov');
    const selCan=document.getElementById('can');
    const selPar=document.getElementById('par');
    const provincias=[...new Set(geojsonData.features.map(f=>f.properties.DPA_DESPRO))].sort();
    provincias.forEach(p=>selProv.add(new Option(p,p)));

    selProv.onchange=()=>{
        selCan.innerHTML='<option value="">Cantón...</option>';
        selPar.innerHTML='<option value="">Parroquia...</option>';
        selCan.disabled=!selProv.value; selPar.disabled=true;
        if(selProv.value){
            const f=geojsonData.features.filter(x=>x.properties.DPA_DESPRO===selProv.value);
            [...new Set(f.map(x=>x.properties.DPA_DESCAN))].sort().forEach(c=>selCan.add(new Option(c,c)));
            map.fitBounds(L.geoJson(f).getBounds());
        }
    };
    selCan.onchange=()=>{
        selPar.innerHTML='<option value="">Parroquia...</option>';
        selPar.disabled=!selCan.value;
        if(selCan.value){
            const f=geojsonData.features.filter(x=>x.properties.DPA_DESPRO===selProv.value && x.properties.DPA_DESCAN===selCan.value);
            f.sort((a,b)=>a.properties.DPA_DESPAR.localeCompare(b.properties.DPA_DESPAR))
             .forEach(x=>selPar.add(new Option(x.properties.DPA_DESPAR,x.properties.DPA_PARROQ)));
            map.fitBounds(L.geoJson(f).getBounds());
        }
    };
    selPar.onchange=()=>{
        geoLayer.eachLayer(l=>{
            if(l.feature.properties.DPA_PARROQ===selPar.value){
                map.fitBounds(l.getBounds()); l.openPopup();
            }
        });
    };
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
