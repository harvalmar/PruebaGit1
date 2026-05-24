from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Precios de referencia en USD/m² (actualizables)
PRECIOS = {
    "construccion_seca": {
        "estructura_perfiles":     8.50,   # Perfiles metálicos (montantes/soleras)
        "placa_yeso_simple":       6.00,   # Placa de yeso estándar 12.5mm
        "placa_yeso_doble":       11.00,   # Dos capas de placa
        "aislamiento_lana_vidrio": 4.50,   # Lana de vidrio 50mm
        "masilla_cinta":           2.00,   # Terminación y pintura base
        "mano_obra":              18.00,   # Mano de obra especializada
    },
    "light_steel_framing": {
        "perfiles_acero":         14.00,   # Perfiles LSF galvanizados
        "osb_revestimiento":       9.00,   # Placa OSB estructural
        "placa_cemento":          10.50,   # Placa cementicia exterior
        "aislamiento_poliestireno": 6.00,  # EPS/Poliestireno expandido
        "membrana_hidrofuga":      3.50,   # Barrera de vapor/agua
        "tornilleria_conectores":  2.50,   # Fijaciones y conectores
        "mano_obra":              22.00,   # Mano de obra especializada LSF
    }
}

INDIRECTOS_PCT = 0.20   # 20% sobre costos directos (gastos generales, utilidad)
IVA_PCT        = 0.21   # 21% IVA (ajustable por país)


def calcular_construccion_seca(area_m2, tipo_placa, con_aislamiento, pisos):
    p = PRECIOS["construccion_seca"]
    detalle = {}

    detalle["Estructura (perfiles metálicos)"] = area_m2 * p["estructura_perfiles"] * pisos
    detalle["Placa de yeso"] = area_m2 * (
        p["placa_yeso_doble"] if tipo_placa == "doble" else p["placa_yeso_simple"]
    ) * pisos

    if con_aislamiento:
        detalle["Aislamiento (lana de vidrio)"] = area_m2 * p["aislamiento_lana_vidrio"] * pisos

    detalle["Masilla, cinta y terminación"] = area_m2 * p["masilla_cinta"] * pisos
    detalle["Mano de obra"] = area_m2 * p["mano_obra"] * pisos

    return detalle


def calcular_lsf(area_m2, revestimiento_ext, con_aislamiento, pisos):
    p = PRECIOS["light_steel_framing"]
    detalle = {}

    detalle["Perfiles de acero galvanizado"] = area_m2 * p["perfiles_acero"] * pisos
    detalle["OSB estructural (interior)"] = area_m2 * p["osb_revestimiento"] * pisos

    if revestimiento_ext == "cemento":
        detalle["Placa cementicia (exterior)"] = area_m2 * p["placa_cemento"] * pisos
    else:
        detalle["OSB exterior"] = area_m2 * p["osb_revestimiento"] * pisos

    if con_aislamiento:
        detalle["Aislamiento (EPS/Poliestireno)"] = area_m2 * p["aislamiento_poliestireno"] * pisos

    detalle["Membrana hidrófuga"] = area_m2 * p["membrana_hidrofuga"] * pisos
    detalle["Tornillería y conectores"] = area_m2 * p["tornilleria_conectores"] * pisos
    detalle["Mano de obra especializada"] = area_m2 * p["mano_obra"] * pisos

    return detalle


def resumen_financiero(detalle):
    costo_directo = sum(detalle.values())
    indirectos    = costo_directo * INDIRECTOS_PCT
    subtotal      = costo_directo + indirectos
    iva           = subtotal * IVA_PCT
    total         = subtotal + iva
    return {
        "costo_directo": costo_directo,
        "indirectos":    indirectos,
        "subtotal":      subtotal,
        "iva":           iva,
        "total":         total,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calcular", methods=["POST"])
def calcular():
    tecnica          = request.form.get("tecnica")
    area_m2          = float(request.form.get("area_m2", 0))
    pisos            = int(request.form.get("pisos", 1))
    con_aislamiento  = request.form.get("aislamiento") == "si"

    if area_m2 <= 0:
        return render_template("index.html", error="El área debe ser mayor a 0 m².")

    if tecnica == "seca":
        tipo_placa = request.form.get("tipo_placa", "simple")
        detalle    = calcular_construccion_seca(area_m2, tipo_placa, con_aislamiento, pisos)
        nombre     = "Construcción en Seco (Drywall)"
        opciones   = {"Tipo de placa": "Doble" if tipo_placa == "doble" else "Simple"}
    else:
        rev_ext  = request.form.get("revestimiento_ext", "cemento")
        detalle  = calcular_lsf(area_m2, rev_ext, con_aislamiento, pisos)
        nombre   = "Light Steel Framing (LSF)"
        opciones = {"Revestimiento exterior": "Placa cementicia" if rev_ext == "cemento" else "OSB"}

    resumen = resumen_financiero(detalle)

    return render_template(
        "resultado.html",
        tecnica=nombre,
        area_m2=area_m2,
        pisos=pisos,
        con_aislamiento=con_aislamiento,
        detalle=detalle,
        resumen=resumen,
        opciones=opciones,
        costo_m2=resumen["total"] / area_m2,
    )


@app.route("/api/calcular", methods=["POST"])
def api_calcular():
    """Endpoint JSON para integraciones externas."""
    data             = request.get_json()
    tecnica          = data.get("tecnica")
    area_m2          = float(data.get("area_m2", 0))
    pisos            = int(data.get("pisos", 1))
    con_aislamiento  = data.get("aislamiento", False)

    if area_m2 <= 0:
        return jsonify({"error": "área_m2 debe ser mayor a 0"}), 400

    if tecnica == "seca":
        tipo_placa = data.get("tipo_placa", "simple")
        detalle    = calcular_construccion_seca(area_m2, tipo_placa, con_aislamiento, pisos)
    elif tecnica == "lsf":
        rev_ext = data.get("revestimiento_ext", "cemento")
        detalle = calcular_lsf(area_m2, rev_ext, con_aislamiento, pisos)
    else:
        return jsonify({"error": "tecnica debe ser 'seca' o 'lsf'"}), 400

    resumen = resumen_financiero(detalle)
    return jsonify({
        "tecnica":   tecnica,
        "area_m2":   area_m2,
        "pisos":     pisos,
        "detalle":   detalle,
        "resumen":   resumen,
        "costo_m2":  resumen["total"] / area_m2,
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
