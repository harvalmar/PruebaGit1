import math
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Precios de referencia en USD/m² — actualiza según cotizaciones locales
# ---------------------------------------------------------------------------
PRECIOS = {
    "construccion_seca": {
        "estructura_perfiles":      8.50,
        "placa_yeso_simple":        6.00,
        "placa_yeso_doble":        11.00,
        "aislamiento_lana_vidrio":  4.50,
        "masilla_cinta":            2.00,
        "tornilleria":              1.50,
        "mano_obra":               18.00,
    },
    "lsf_muros": {
        # Estructura
        "perfiles_acero":          14.00,   # Montantes + soleras galvanizadas
        # Capas exteriores
        "osb_exterior":             9.00,   # OSB estructural
        "membrana_hidrofuga":       3.50,   # Housewrap
        "rastreles_fachada":        2.80,   # Listones cámara ventilada (4 cm)
        "fibrocemento":             8.50,   # Láminas fibrocemento 6–8 mm
        "eps_3cm_fachada":          5.00,   # EPS 3 cm entre rastreles (opcional)
        # Aislamiento dentro del perfil
        "lana_de_roca":             7.50,   # Lana de roca 50 mm
        # Interior
        "barrera_vapor":            2.00,   # Membrana polietileno cara interior
        "drywall":                  6.00,   # Placa yeso 12.5 mm
        "mdf_melamínico":          12.00,   # MDF/MDP con melamina
        # Acabados exteriores sobre fibrocemento
        "estuco":                   4.00,
        "graniplast":               8.00,
        "granimarmol":             10.00,
        "vinilico":                15.00,   # Vinyl siding / PVC flexible
        # Tornillería y anclajes
        "tornillos_estructura":     2.50,   # Tornillos LB autoperforantes LSF
        "tornillos_osb":            1.20,   # Tornillos para OSB
        "tornillos_fibrocemento":   1.80,   # Anti-corrosión para fibrocemento
        "anclajes_fundacion":       3.00,   # Pernos / anclajes químicos a platea
        "conectores_sismicos":      2.50,   # Straps y ángulos sísmicos
        "mano_obra":               22.00,
    },
    "lsf_techo": {
        # Estructura base
        "osb_techo":                9.00,   # OSB base del techo
        "membrana_hidrofuga":       3.50,   # Membrana hidrófuga sobre OSB
        "rastreles_techo":          2.80,   # Listones apoyo teja (4 cm)
        "eps_3cm_techo":            5.00,   # EPS 3 cm entre rastreles (opcional)
        "teja_acero_galv":         13.00,   # Teja acero galvanizado pintado
        # Techo plano
        "membrana_impermeab":      14.00,   # EPDM / lámina bituminosa
        # Extra dos aguas
        "remate_cumbrera":          2.00,   # Viga cumbrera + tapajuntas
        # Tornillería techo
        "tornillos_techo":          2.00,   # Para OSB y teja
        "ganchos_teja":             1.50,   # Ganchos y anclajes de teja
        # Mano de obra
        "mano_obra_inclinado":     20.00,   # MO techo inclinado
        "mano_obra_plano":         16.00,   # MO techo plano
    },
}

INDIRECTOS_PCT = 0.20   # 20% gastos generales y utilidad
IVA_PCT        = 0.19   # 19% IVA Colombia

ACABADOS_NOMBRES = {
    "estuco":      "Estuco sobre fibrocemento",
    "graniplast":  "Graniplast",
    "granimarmol": "Granimármol",
    "vinilico":    "Revestimiento vinílico (vinyl siding)",
}

TECHO_NOMBRES = {
    "plano":      "Plano",
    "un_agua":    "A un agua",
    "dos_aguas":  "A dos aguas",
}


# ---------------------------------------------------------------------------
# Funciones de cálculo
# ---------------------------------------------------------------------------

def factor_pendiente(pendiente_pct: float) -> float:
    """Convierte pendiente en % al factor de área real vs proyección horizontal."""
    return 1.0 / math.cos(math.atan(pendiente_pct / 100.0))


def calcular_construccion_seca(area_m2, tipo_placa, con_aislamiento, pisos):
    p = PRECIOS["construccion_seca"]
    detalle = {}
    detalle["Estructura (perfiles metálicos)"] = area_m2 * p["estructura_perfiles"] * pisos
    detalle["Placa de yeso"] = area_m2 * (
        p["placa_yeso_doble"] if tipo_placa == "doble" else p["placa_yeso_simple"]
    ) * pisos
    if con_aislamiento:
        detalle["Aislamiento (lana de vidrio)"]          = area_m2 * p["aislamiento_lana_vidrio"] * pisos
    detalle["Masilla, cinta y terminación"]              = area_m2 * p["masilla_cinta"]  * pisos
    detalle["Tornillería (autoperforantes y tacos)"]     = area_m2 * p["tornilleria"]    * pisos
    detalle["Mano de obra"]                              = area_m2 * p["mano_obra"]      * pisos
    return detalle


def calcular_lsf_muros(area_m2, rev_interior, acabado_ext,
                        con_lana_roca, con_eps_fachada, pisos):
    p = PRECIOS["lsf_muros"]
    d = {}
    # Estructura
    d["Perfiles de acero galvanizado (montantes y soleras)"] = area_m2 * p["perfiles_acero"]     * pisos
    # Capas exteriores
    d["OSB estructural (revestimiento exterior)"]            = area_m2 * p["osb_exterior"]       * pisos
    d["Membrana hidrófuga (housewrap)"]                      = area_m2 * p["membrana_hidrofuga"] * pisos
    d["Rastreles de fijación 4 cm (cámara ventilada)"]       = area_m2 * p["rastreles_fachada"]  * pisos
    if con_eps_fachada:
        d["EPS 3 cm entre rastreles (fachada)"]              = area_m2 * p["eps_3cm_fachada"]    * pisos
    d["Láminas de fibrocemento (fachada ventilada)"]         = area_m2 * p["fibrocemento"]       * pisos
    # Aislamiento dentro del perfil
    if con_lana_roca:
        d["Lana de roca (aislamiento térmico y acústico)"]   = area_m2 * p["lana_de_roca"]       * pisos
    # Interior
    d["Barrera de vapor (cara interior del muro)"]           = area_m2 * p["barrera_vapor"]      * pisos
    if rev_interior == "mdf":
        d["Revestimiento interior — MDF/MDP melamínico"]     = area_m2 * p["mdf_melamínico"]     * pisos
    else:
        d["Revestimiento interior — Drywall 12.5 mm"]        = area_m2 * p["drywall"]            * pisos
    # Acabado exterior
    nombre_ac = f"Acabado exterior — {ACABADOS_NOMBRES.get(acabado_ext, acabado_ext)}"
    d[nombre_ac]                                             = area_m2 * p.get(acabado_ext, p["estuco"]) * pisos
    # Tornillería y anclajes
    d["Tornillos LB autoperforantes (estructura LSF)"]       = area_m2 * p["tornillos_estructura"]   * pisos
    d["Tornillos para OSB (cabeza plana)"]                   = area_m2 * p["tornillos_osb"]          * pisos
    d["Tornillos para fibrocemento (galvanizados)"]          = area_m2 * p["tornillos_fibrocemento"] * pisos
    d["Anclajes a fundación (pernos / anclajes químicos)"]   = area_m2 * p["anclajes_fundacion"]     * pisos
    d["Conectores sísmicos (straps y ángulos)"]              = area_m2 * p["conectores_sismicos"]    * pisos
    d["Mano de obra especializada — muros"]                  = area_m2 * p["mano_obra"]              * pisos
    return d


def calcular_lsf_techo(area_m2_planta, tipo_techo, pendiente_pct, con_eps_techo):
    """
    area_m2_planta : área en planta (proyección horizontal)
    tipo_techo     : 'plano' | 'un_agua' | 'dos_aguas'
    pendiente_pct  : pendiente en % (ej: 25.0)
    con_eps_techo  : bool
    Devuelve (detalle_dict, area_real, factor_area)
    """
    p = PRECIOS["lsf_techo"]
    d = {}

    if tipo_techo == "plano":
        area_real  = area_m2_planta
        factor     = 1.0
        d["OSB estructural (base techo plano)"]                 = area_real * p["osb_techo"]
        d["Membrana impermeabilizante (EPDM / bituminosa)"]     = area_real * p["membrana_impermeab"]
        d["Tornillería y anclajes (techo plano)"]               = area_real * p["tornillos_techo"]
        d["Mano de obra — techo plano"]                         = area_real * p["mano_obra_plano"]
    else:
        factor     = factor_pendiente(pendiente_pct)
        area_real  = area_m2_planta * factor
        d["OSB estructural (base techo)"]                       = area_real * p["osb_techo"]
        d["Membrana hidrófuga (sobre OSB del techo)"]           = area_real * p["membrana_hidrofuga"]
        d["Rastreles de apoyo 4 cm (tejado)"]                   = area_real * p["rastreles_techo"]
        if con_eps_techo:
            d["EPS 3 cm entre rastreles (aislamiento techo)"]   = area_real * p["eps_3cm_techo"]
        d["Teja de acero galvanizado pintado"]                  = area_real * p["teja_acero_galv"]
        if tipo_techo == "dos_aguas":
            d["Remate de cumbrera (viga ridge + tapajuntas)"]   = area_m2_planta * p["remate_cumbrera"]
        d["Tornillos y ganchos para tejado"]                    = area_real * (p["tornillos_techo"] + p["ganchos_teja"])
        d["Mano de obra — techo inclinado"]                     = area_real * p["mano_obra_inclinado"]

    return d, area_real, factor


def resumen_financiero(detalle_muros: dict, detalle_techo: dict) -> dict:
    cd_muros  = sum(detalle_muros.values())
    cd_techo  = sum(detalle_techo.values())
    cd_total  = cd_muros + cd_techo
    indirectos = cd_total * INDIRECTOS_PCT
    subtotal   = cd_total + indirectos
    iva        = subtotal * IVA_PCT
    total      = subtotal + iva
    return {
        "cd_muros":    cd_muros,
        "cd_techo":    cd_techo,
        "costo_directo": cd_total,
        "indirectos":  indirectos,
        "subtotal":    subtotal,
        "iva":         iva,
        "total":       total,
    }


# ---------------------------------------------------------------------------
# Rutas Flask
# ---------------------------------------------------------------------------

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
    if pisos < 1 or pisos > 2:
        return render_template("index.html", error="La normativa colombiana limita a máximo 2 pisos.")

    if tecnica == "seca":
        tipo_placa     = request.form.get("tipo_placa", "simple")
        detalle_muros  = calcular_construccion_seca(area_m2, tipo_placa, con_aislamiento, pisos)
        detalle_techo  = {}
        nombre         = "Construcción en Seco (Drywall)"
        opciones       = {"Placa": "Doble (2 capas)" if tipo_placa == "doble" else "Simple (1 capa)"}
        info_techo     = None

    else:
        rev_interior    = request.form.get("rev_interior", "drywall")
        acabado_ext     = request.form.get("acabado_ext", "estuco")
        con_eps_fachada = request.form.get("eps_fachada") == "si"
        tipo_techo      = request.form.get("tipo_techo", "dos_aguas")
        pendiente_pct   = float(request.form.get("pendiente_pct", 25))
        con_eps_techo   = request.form.get("eps_techo") == "si"

        detalle_muros   = calcular_lsf_muros(
            area_m2, rev_interior, acabado_ext, con_aislamiento, con_eps_fachada, pisos
        )
        detalle_techo, area_techo_real, factor = calcular_lsf_techo(
            area_m2, tipo_techo, pendiente_pct, con_eps_techo
        )
        nombre  = "Light Steel Framing (LSF)"
        opciones = {
            "Interior":        "MDF/MDP melamínico" if rev_interior == "mdf" else "Drywall",
            "Acabado ext.":    ACABADOS_NOMBRES.get(acabado_ext, acabado_ext),
            "EPS fachada":     "Sí" if con_eps_fachada else "No",
        }
        info_techo = {
            "tipo":         TECHO_NOMBRES.get(tipo_techo, tipo_techo),
            "pendiente":    f"{pendiente_pct:.0f}%" if tipo_techo != "plano" else "—",
            "area_real":    round(area_techo_real, 2),
            "factor":       round(factor, 3),
            "con_eps":      con_eps_techo,
        }

    resumen   = resumen_financiero(detalle_muros, detalle_techo)
    area_total = area_m2 * pisos

    return render_template(
        "resultado.html",
        tecnica       = nombre,
        area_m2       = area_m2,
        pisos         = pisos,
        con_aislamiento = con_aislamiento,
        opciones      = opciones,
        detalle_muros = detalle_muros,
        detalle_techo = detalle_techo,
        info_techo    = info_techo,
        resumen       = resumen,
        costo_m2      = resumen["total"] / area_total,
    )


@app.route("/api/calcular", methods=["POST"])
def api_calcular():
    """Endpoint JSON para integraciones externas."""
    data             = request.get_json()
    tecnica          = data.get("tecnica")
    area_m2          = float(data.get("area_m2", 0))
    pisos            = int(data.get("pisos", 1))
    con_aislamiento  = data.get("aislamiento", True)

    if area_m2 <= 0:
        return jsonify({"error": "area_m2 debe ser mayor a 0"}), 400
    if pisos < 1 or pisos > 2:
        return jsonify({"error": "La normativa colombiana limita a máximo 2 pisos"}), 400

    if tecnica == "seca":
        tipo_placa    = data.get("tipo_placa", "simple")
        detalle_muros = calcular_construccion_seca(area_m2, tipo_placa, con_aislamiento, pisos)
        detalle_techo = {}
    elif tecnica == "lsf":
        rev_interior    = data.get("rev_interior", "drywall")
        acabado_ext     = data.get("acabado_ext", "estuco")
        con_eps_fachada = data.get("eps_fachada", False)
        tipo_techo      = data.get("tipo_techo", "dos_aguas")
        pendiente_pct   = float(data.get("pendiente_pct", 25))
        con_eps_techo   = data.get("eps_techo", False)
        detalle_muros   = calcular_lsf_muros(
            area_m2, rev_interior, acabado_ext, con_aislamiento, con_eps_fachada, pisos
        )
        detalle_techo, area_techo_real, factor = calcular_lsf_techo(
            area_m2, tipo_techo, pendiente_pct, con_eps_techo
        )
    else:
        return jsonify({"error": "tecnica debe ser 'seca' o 'lsf'"}), 400

    resumen = resumen_financiero(detalle_muros, detalle_techo)
    return jsonify({
        "tecnica":       tecnica,
        "area_m2":       area_m2,
        "pisos":         pisos,
        "detalle_muros": detalle_muros,
        "detalle_techo": detalle_techo,
        "resumen":       resumen,
        "costo_m2":      resumen["total"] / (area_m2 * pisos),
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
