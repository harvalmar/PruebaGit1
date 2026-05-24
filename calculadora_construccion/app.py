from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Precios de referencia en USD/m² — actualiza según cotizaciones locales
PRECIOS = {
    "construccion_seca": {
        "estructura_perfiles":      8.50,   # Perfiles metálicos (montantes/soleras)
        "placa_yeso_simple":        6.00,   # Placa de yeso estándar 12.5 mm
        "placa_yeso_doble":        11.00,   # Dos capas de placa
        "aislamiento_lana_vidrio":  4.50,   # Lana de vidrio 50 mm
        "masilla_cinta":            2.00,   # Terminación y pintura base
        "tornilleria":              1.50,   # Tornillos autoperforrantes y tacos
        "mano_obra":               18.00,   # Mano de obra especializada
    },
    "lsf": {
        # Estructura principal
        "perfiles_acero":          14.00,   # Montantes + soleras galvanizadas

        # Capas del muro: exterior → interior
        "osb_exterior":             9.00,   # OSB estructural (revestimiento ext.)
        "membrana_hidrofuga":       3.50,   # Housewrap / barrera de agua
        "rastreles_fachada":        2.80,   # Listones que crean la cámara ventilada
        "fibrocemento":             8.50,   # Láminas fibrocemento 6–8 mm

        # Aislamiento dentro del perfil
        "lana_de_roca":             7.50,   # Lana de roca 50 mm (mejor que EPS en fuego/acústica)

        # Interior del muro
        "barrera_vapor":            2.00,   # Membrana polietileno cara interior

        # Revestimiento interior — seleccionable por el cliente
        "drywall":                  6.00,   # Placa de yeso 12.5 mm
        "mdf_melamínico":          12.00,   # MDF/MDP con recubrimiento melamínico

        # Acabados exteriores sobre fibrocemento — seleccionable por el cliente
        "estuco":                   4.00,   # Estuco sobre fibrocemento
        "graniplast":               8.00,   # Graniplast (textura acrílica)
        "granimarmol":             10.00,   # Granimármol (efecto mármol)
        "vinilico":                15.00,   # Vinyl siding / revestimiento PVC flexible

        # Tornillería y anclajes — desglosado por uso
        "tornillos_estructura":     2.50,   # Tornillos LB autoperforantes para perfiles LSF
        "tornillos_osb":            1.20,   # Tornillos cabeza plana para OSB
        "tornillos_fibrocemento":   1.80,   # Tornillos inox/galv. para fibrocemento
        "anclajes_fundacion":       3.00,   # Pernos de anclaje / anclajes químicos a platea
        "conectores_sismicos":      2.50,   # Straps, ángulos y rigidizadores sísmicos

        # Mano de obra
        "mano_obra":               22.00,   # Mano de obra especializada LSF
    }
}

INDIRECTOS_PCT = 0.20   # 20% — gastos generales y utilidad del contratista
IVA_PCT        = 0.19   # 19% IVA Colombia (ajustar según país)

ACABADOS_NOMBRES = {
    "estuco":      "Acabado exterior — Estuco sobre fibrocemento",
    "graniplast":  "Acabado exterior — Graniplast",
    "granimarmol": "Acabado exterior — Granimármol",
    "vinilico":    "Acabado exterior — Revestimiento vinílico (vinyl siding)",
}


def calcular_construccion_seca(area_m2, tipo_placa, con_aislamiento, pisos):
    p = PRECIOS["construccion_seca"]
    detalle = {}

    detalle["Estructura (perfiles metálicos)"] = area_m2 * p["estructura_perfiles"] * pisos
    detalle["Placa de yeso"] = area_m2 * (
        p["placa_yeso_doble"] if tipo_placa == "doble" else p["placa_yeso_simple"]
    ) * pisos

    if con_aislamiento:
        detalle["Aislamiento (lana de vidrio)"] = area_m2 * p["aislamiento_lana_vidrio"] * pisos

    detalle["Masilla, cinta y terminación"]         = area_m2 * p["masilla_cinta"]  * pisos
    detalle["Tornillería (autoperforantes y tacos)"] = area_m2 * p["tornilleria"]   * pisos
    detalle["Mano de obra"]                          = area_m2 * p["mano_obra"]     * pisos

    return detalle


def calcular_lsf(area_m2, rev_interior, acabado_ext, con_aislamiento, pisos):
    p = PRECIOS["lsf"]
    detalle = {}

    # ── Estructura ───────────────────────────────────────────────────────────
    detalle["Perfiles de acero galvanizado (montantes y soleras)"] = (
        area_m2 * p["perfiles_acero"] * pisos
    )

    # ── Capas del muro exterior ──────────────────────────────────────────────
    detalle["OSB estructural (revestimiento exterior)"]   = area_m2 * p["osb_exterior"]      * pisos
    detalle["Membrana hidrófuga (housewrap)"]              = area_m2 * p["membrana_hidrofuga"] * pisos
    detalle["Rastreles de fijación (cámara ventilada)"]   = area_m2 * p["rastreles_fachada"]  * pisos
    detalle["Láminas de fibrocemento (fachada ventilada)"] = area_m2 * p["fibrocemento"]       * pisos

    # ── Aislamiento dentro del perfil ────────────────────────────────────────
    if con_aislamiento:
        detalle["Lana de roca (aislamiento térmico y acústico)"] = (
            area_m2 * p["lana_de_roca"] * pisos
        )

    # ── Interior ─────────────────────────────────────────────────────────────
    detalle["Barrera de vapor (cara interior del muro)"] = area_m2 * p["barrera_vapor"] * pisos

    if rev_interior == "mdf":
        detalle["Revestimiento interior — MDF/MDP melamínico"] = (
            area_m2 * p["mdf_melamínico"] * pisos
        )
    else:
        detalle["Revestimiento interior — Drywall (placa de yeso 12.5 mm)"] = (
            area_m2 * p["drywall"] * pisos
        )

    # ── Acabado exterior sobre fibrocemento ──────────────────────────────────
    nombre_acabado = ACABADOS_NOMBRES.get(acabado_ext, "Acabado exterior")
    detalle[nombre_acabado] = area_m2 * p.get(acabado_ext, p["estuco"]) * pisos

    # ── Tornillería y anclajes ───────────────────────────────────────────────
    detalle["Tornillos LB autoperforantes (estructura LSF)"]    = area_m2 * p["tornillos_estructura"]  * pisos
    detalle["Tornillos para OSB (cabeza plana)"]                 = area_m2 * p["tornillos_osb"]         * pisos
    detalle["Tornillos para fibrocemento (galvanizados)"]        = area_m2 * p["tornillos_fibrocemento"] * pisos
    detalle["Anclajes a fundación (pernos / anclajes químicos)"] = area_m2 * p["anclajes_fundacion"]    * pisos
    detalle["Conectores sísmicos (straps y ángulos)"]            = area_m2 * p["conectores_sismicos"]   * pisos

    # ── Mano de obra ─────────────────────────────────────────────────────────
    detalle["Mano de obra especializada LSF"] = area_m2 * p["mano_obra"] * pisos

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
    tecnica         = request.form.get("tecnica")
    area_m2         = float(request.form.get("area_m2", 0))
    pisos           = int(request.form.get("pisos", 1))
    con_aislamiento = request.form.get("aislamiento") == "si"

    if area_m2 <= 0:
        return render_template("index.html", error="El área debe ser mayor a 0 m².")
    if pisos < 1 or pisos > 2:
        return render_template("index.html", error="La normativa colombiana limita a máximo 2 pisos.")

    if tecnica == "seca":
        tipo_placa = request.form.get("tipo_placa", "simple")
        detalle    = calcular_construccion_seca(area_m2, tipo_placa, con_aislamiento, pisos)
        nombre     = "Construcción en Seco (Drywall)"
        opciones   = {"Tipo de placa": "Doble (2 capas)" if tipo_placa == "doble" else "Simple (1 capa)"}

    else:
        rev_interior = request.form.get("rev_interior", "drywall")
        acabado_ext  = request.form.get("acabado_ext", "estuco")
        detalle      = calcular_lsf(area_m2, rev_interior, acabado_ext, con_aislamiento, pisos)
        nombre       = "Light Steel Framing (LSF)"
        opciones     = {
            "Interior": "MDF/MDP melamínico" if rev_interior == "mdf" else "Drywall",
            "Acabado exterior": ACABADOS_NOMBRES.get(acabado_ext, acabado_ext).split("—")[-1].strip(),
        }

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
    data            = request.get_json()
    tecnica         = data.get("tecnica")
    area_m2         = float(data.get("area_m2", 0))
    pisos           = int(data.get("pisos", 1))
    con_aislamiento = data.get("aislamiento", True)

    if area_m2 <= 0:
        return jsonify({"error": "area_m2 debe ser mayor a 0"}), 400
    if pisos < 1 or pisos > 2:
        return jsonify({"error": "La normativa colombiana limita a máximo 2 pisos"}), 400

    if tecnica == "seca":
        tipo_placa = data.get("tipo_placa", "simple")
        detalle    = calcular_construccion_seca(area_m2, tipo_placa, con_aislamiento, pisos)
    elif tecnica == "lsf":
        rev_interior = data.get("rev_interior", "drywall")
        acabado_ext  = data.get("acabado_ext", "estuco")
        detalle      = calcular_lsf(area_m2, rev_interior, acabado_ext, con_aislamiento, pisos)
    else:
        return jsonify({"error": "tecnica debe ser 'seca' o 'lsf'"}), 400

    resumen = resumen_financiero(detalle)
    return jsonify({
        "tecnica":  tecnica,
        "area_m2":  area_m2,
        "pisos":    pisos,
        "detalle":  detalle,
        "resumen":  resumen,
        "costo_m2": resumen["total"] / area_m2,
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
