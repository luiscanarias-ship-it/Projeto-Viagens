"""
Hybrid Travel Plan Engine — Template + AI Layer
Reduces LLM costs by 70-90% using deterministic templates for known data
and reserving AI only for personalization and creative content.

Architecture:
  Layer 1: Exact cache (MongoDB) → 0 cost
  Layer 2: Fuzzy cache (same destination, different dates) → 0 cost
  Layer 3: Specific destination template → 0 cost (19 cities)
  Layer 4: Template type fallback (european_city_break, beach, long_haul) → 0 cost
  Layer 5: Full AI (GPT-5.2) → LLM cost (only for unknown destinations)
"""
from datetime import datetime, timedelta
from destination_data import (
    DESTINATIONS, DESTINATION_ALIASES, TEMPLATE_TYPES,
    WEATHER_TEMPLATES, PACKING_TEMPLATES, CHECKLIST_TEMPLATE,
)


def match_destination(query: str) -> dict | None:
    """Fuzzy match destination query against knowledge base."""
    q = query.lower().strip()
    if q in DESTINATION_ALIASES:
        return DESTINATIONS.get(DESTINATION_ALIASES[q])
    for alias, key in DESTINATION_ALIASES.items():
        if alias in q or q in alias:
            return DESTINATIONS.get(key)
    return None


def match_template_type(query: str, num_days: int) -> dict | None:
    """Match a destination to a generic template type when no specific template exists.
    Uses heuristics: duration, keywords in the query."""
    q = query.lower().strip()

    beach_keywords = ["praia", "beach", "ilha", "island", "costa", "resort", "tropical", "caribe", "caribbean", "maldivas", "maldives", "cancun", "phuket", "zanzibar", "mauricias", "seychelles", "cabo verde", "acores", "madeira", "canarias", "tenerife", "ibiza", "mykonos", "santorini", "creta", "crete", "sicilia", "sardinia", "algarve"]
    long_haul_keywords = ["japao", "japan", "coreia", "korea", "china", "tailandia", "thailand", "vietnam", "india", "brasil", "brazil", "mexico", "peru", "argentina", "colombia", "australia", "nova zelandia", "new zealand", "africa", "marrocos", "morocco", "egito", "egypt", "eua", "usa", "estados unidos", "canada", "singapura", "singapore", "hong kong", "taiwan"]

    for kw in beach_keywords:
        if kw in q:
            return TEMPLATE_TYPES["beach_destination"]
    for kw in long_haul_keywords:
        if kw in q:
            return TEMPLATE_TYPES["long_haul_trip"]
    if num_days <= 5:
        return TEMPLATE_TYPES["european_city_break"]
    return TEMPLATE_TYPES["european_city_break"]


def get_weather(zone: str, start_date: str, end_date: str) -> str:
    """Generate weather description from templates."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        month = start.month
    except ValueError:
        month = 6
    templates = WEATHER_TEMPLATES.get(zone, WEATHER_TEMPLATES["continental"])
    return templates.get(month, "Clima variavel. Leva camadas e impermeavel.")


def get_packing(zone: str, month: int) -> dict:
    """Get packing list based on climate zone and month."""
    if zone == "desert":
        return PACKING_TEMPLATES["hot_dry"]
    if zone == "tropical":
        return PACKING_TEMPLATES["tropical"]
    if zone in ("mediterranean", "humid_subtropical") and month in (5, 6, 7, 8, 9):
        return PACKING_TEMPLATES["warm"]
    if zone in ("continental", "humid_continental", "oceanic") and month in (11, 12, 1, 2):
        return PACKING_TEMPLATES["cold"]
    return PACKING_TEMPLATES["mild"]


def get_flight_info(dest_data: dict, start_date: str, end_date: str) -> dict:
    """Generate flight SEARCH suggestion listing all real airports."""
    airports = dest_data.get("airports", [])
    if not airports:
        return None
    airport_list = [
        {"code": ap["code"], "name": ap["name"], "distance": ap.get("distance", ""), "transport": ap.get("transport", "")}
        for ap in airports
    ]
    return {
        "suggestion": True,
        "airports": airport_list,
        "tip": f"Compara precos entre todos os aeroportos de {dest_data['name']}. Voos para aeroportos secundarios podem ser mais baratos mas ficam mais longe do centro. [CTA:flight:Comparar voos]",
    }


def get_must_see(dest_data: dict, num_days: int) -> list:
    """Return must-see monuments filtered by available days.
    Rule: ~2 major sights per day, minimum 3, maximum all."""
    all_sights = dest_data.get("must_see", [])
    if not all_sights:
        return []
    max_sights = max(3, min(num_days * 2, len(all_sights)))
    return all_sights[:max_sights]


def get_stay_zones(dest_data: dict) -> list:
    """Return recommended stay zones with transport info."""
    return dest_data.get("stay_zones", [])


def build_template_itinerary(dest_data: dict, num_days: int) -> list:
    """Build a deterministic itinerary from the knowledge base."""
    attractions = dest_data.get("attractions", {})
    iconic = attractions.get("iconic", [])
    cultural = attractions.get("cultural", [])
    local = attractions.get("local", [])
    food = attractions.get("food", [])

    itinerary = []

    # Day 1: Arrival + iconic
    day1_acts = []
    if iconic:
        day1_acts.append(f"Chegada e check-in no hotel ({dest_data.get('hotel_area', 'centro')})")
        day1_acts.append(iconic[0] if iconic else "Explorar o centro")
        if food:
            day1_acts.append(food[0])
        if local:
            day1_acts.append(f"Passeio por {local[0].split('(')[0].strip()}")
    itinerary.append({"day": 1, "title": f"Chegada a {dest_data['name']}", "activities": day1_acts[:4]})

    # Middle days: mix of iconic, cultural, local
    pools = [iconic[1:], cultural, local[1:], food[1:]]

    for d in range(2, num_days):
        acts = []
        day_title = ""

        if d == 2 and len(iconic) > 1:
            acts = [iconic[1]]
            if cultural:
                acts.append(cultural[0])
            if len(local) > 1:
                acts.append(local[1])
            if len(food) > 1:
                acts.append(food[1])
            day_title = f"Icones de {dest_data['name']}"
        elif d == 3 and len(cultural) > 1:
            acts = [cultural[min(1, len(cultural) - 1)]]
            if len(iconic) > 2:
                acts.append(iconic[2])
            if len(local) > 2:
                acts.append(local[2])
            if len(food) > 2:
                acts.append(food[2])
            day_title = "Cultura e descobertas"
        elif d == 4:
            acts = []
            if len(iconic) > 3:
                acts.append(iconic[3])
            if len(cultural) > 2:
                acts.append(cultural[2])
            if len(local) > 3:
                acts.append(local[3])
            if len(food) > 3:
                acts.append(food[3])
            day_title = f"Explorar {dest_data['name']} a fundo"
        elif d == 5:
            acts = []
            if len(iconic) > 4:
                acts.append(iconic[4])
            if len(cultural) > 3:
                acts.append(cultural[3])
            if len(local) > 4:
                acts.append(local[4])
            if len(food) > 4:
                acts.append(food[4])
            day_title = "Tesouros escondidos"
        else:
            for pool in pools:
                if pool and len(acts) < 4:
                    idx = (d - 6) % max(len(pool), 1)
                    if idx < len(pool):
                        acts.append(pool[idx])
            day_title = f"Dia {d}: Explorar {dest_data['name']}"

        if not acts:
            acts = ["Dia livre para explorar ao teu ritmo", "Visita zonas menos turisticas", "Descansa e aproveita a cidade"]
        itinerary.append({"day": d, "title": day_title, "activities": acts[:4]})

    # Last day: departure
    last_acts = ["Check-out do hotel"]
    if local:
        last_acts.append(f"Ultima visita: {local[-1].split('(')[0].strip()}")
    if food:
        last_acts.append(f"Almoco de despedida: {food[-1]}")
    last_acts.append("Transfer para o aeroporto e regresso")
    itinerary.append({"day": num_days, "title": f"Despedida de {dest_data['name']}", "activities": last_acts[:4]})

    return itinerary


def inject_ctas(itinerary: list, tips: list) -> tuple:
    """Inject contextual CTA markers into itinerary and tips (max 5)."""
    cta_count = 0
    max_ctas = 5

    cta_patterns = {
        "museu": "[CTA:activity:Reservar bilhetes]",
        "bilhete": "[CTA:activity:Evita filas — ver bilhetes]",
        "reserva": "[CTA:activity:Reservar com antecedencia]",
        "tour": "[CTA:activity:Reservar tour]",
        "hotel": "[CTA:hotel:Ver hoteis]",
        "alojamento": "[CTA:hotel:Ver hoteis no centro]",
        "voo": "[CTA:flight:Comparar voos]",
        "esim": "[CTA:esim:Ver eSIM]",
        "internet": "[CTA:esim:Comprar eSIM]",
        "seguro": "[CTA:insurance:Fazer seguro]",
        "carro": "[CTA:transport:Ver transportes]",
    }

    used_types = set()

    for day in itinerary:
        new_acts = []
        for act in day.get("activities", []):
            if cta_count < max_ctas:
                act_lower = act.lower()
                for keyword, cta in cta_patterns.items():
                    cta_type = cta.split(":")[1]
                    if keyword in act_lower and cta_type not in used_types:
                        act = f"{act} {cta}"
                        used_types.add(cta_type)
                        cta_count += 1
                        break
            new_acts.append(act)
        day["activities"] = new_acts

    new_tips = []
    for tip in tips:
        if cta_count < max_ctas:
            tip_lower = tip.lower()
            for keyword, cta in cta_patterns.items():
                cta_type = cta.split(":")[1]
                if keyword in tip_lower and cta_type not in used_types:
                    tip = f"{tip} {cta}"
                    used_types.add(cta_type)
                    cta_count += 1
                    break
        new_tips.append(tip)

    return itinerary, new_tips


def build_full_template_plan(dest_data: dict, destination: str, start_date: str, end_date: str) -> dict:
    """Build a complete travel plan from templates (0 AI cost)."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        num_days = max((end - start).days, 1)
    except ValueError:
        num_days = 3
        start = datetime.now()

    itinerary = build_template_itinerary(dest_data, num_days)
    tips = list(dest_data.get("tips", []))
    itinerary, tips = inject_ctas(itinerary, tips)

    weather = get_weather(dest_data["weather_zone"], start_date, end_date)
    packing = get_packing(dest_data["weather_zone"], start.month)
    flight_info = get_flight_info(dest_data, start_date, end_date)
    must_see = get_must_see(dest_data, num_days)
    stay_zones = get_stay_zones(dest_data)

    # Build rich hotel_info with stay zones
    primary_zone = dest_data.get("hotel_area", "centro")
    hotel_tip = f"Recomendamos ficar na zona de {primary_zone} — zona central com bom acesso a transportes e atracoes principais."
    if stay_zones:
        zone_names = ", ".join(z["name"] for z in stay_zones[:3])
        hotel_tip = f"As melhores zonas para ficar sao: {zone_names}. Todas com bom acesso aos transportes que ligam ao aeroporto."
    hotel_tip += " [CTA:hotel:Ver hoteis no centro]"

    plan = {
        "destination": dest_data["name"],
        "dates": f"{start_date} a {end_date}",
        "summary": f"Roteiro de {num_days} dias em {dest_data['name']}, {dest_data['country']}. Descobre o melhor da cidade com este guia pratico.",
        "flight_info": flight_info,
        "hotel_info": {
            "suggestion": True,
            "area": primary_zone,
            "stay_zones": stay_zones,
            "tip": hotel_tip,
        },
        "airport_to_hotel": {
            "airports": dest_data.get("airports", []),
            "tip": dest_data["transport"]["tip"],
        },
        "must_see": must_see,
        "itinerary": itinerary,
        "weather": weather,
        "packing": packing,
        "checklist": CHECKLIST_TEMPLATE,
        "local_tips": tips,
    }

    return plan


def build_type_plan(template_type: dict, destination: str, start_date: str, end_date: str) -> dict:
    """Build a generic plan from a template TYPE (0 AI cost).
    Used as Layer 4 fallback for destinations not in specific templates."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        num_days = max((end - start).days, 1)
    except ValueError:
        num_days = 3
        start = datetime.now()

    structure = template_type.get("structure", {})
    itinerary = []

    for d in range(1, num_days + 1):
        if d == 1:
            acts = list(structure.get("day_1", ["Chegada e check-in"]))
            title = f"Chegada a {destination}"
        elif d == num_days:
            acts = list(structure.get("last_day", ["Check-out e partida"]))
            title = f"Despedida de {destination}"
        elif d == 2:
            acts = list(structure.get("day_2", structure.get("middle", ["Explorar a cidade"])))
            title = f"Descobrir {destination}"
        else:
            acts = list(structure.get("middle", ["Explorar ao teu ritmo"]))
            title = f"Dia {d}: Explorar {destination}"
        itinerary.append({"day": d, "title": title, "activities": acts[:4]})

    zone = template_type.get("weather_zone", "continental")
    weather = get_weather(zone, start_date, end_date)
    packing_key = template_type.get("default_packing", "mild")
    packing = PACKING_TEMPLATES.get(packing_key, PACKING_TEMPLATES["mild"])
    tips = list(template_type.get("generic_tips", []))
    must_see = list(template_type.get("generic_must_see", []))

    return {
        "destination": destination,
        "dates": f"{start_date} a {end_date}",
        "summary": f"Roteiro de {num_days} dias em {destination}. Guia pratico com sugestoes e dicas.",
        "flight_info": {
            "suggestion": True,
            "airports": [],
            "tip": f"Pesquisa voos para {destination} e compara precos entre diferentes aeroportos. [CTA:flight:Comparar voos]",
        },
        "hotel_info": {
            "suggestion": True,
            "area": "centro",
            "stay_zones": [],
            "tip": f"Recomendamos ficar no centro de {destination}, perto de transportes publicos. [CTA:hotel:Ver hoteis no centro]",
        },
        "airport_to_hotel": {
            "airports": [],
            "tip": f"Verifica as opcoes de transporte do aeroporto para o centro de {destination} antes de viajar.",
        },
        "must_see": must_see,
        "itinerary": itinerary,
        "weather": weather,
        "packing": packing,
        "checklist": CHECKLIST_TEMPLATE,
        "local_tips": tips,
        "is_generic_template": True,
    }


def adapt_cached_plan(cached_plan: dict, new_start: str, new_end: str) -> dict:
    """Adapt a cached plan to new dates (deterministic, 0 AI cost)."""
    plan = dict(cached_plan)
    plan["dates"] = f"{new_start} a {new_end}"

    try:
        start = datetime.strptime(new_start, "%Y-%m-%d")
        end = datetime.strptime(new_end, "%Y-%m-%d")
        new_days = max((end - start).days, 1)
        current_days = len(plan.get("itinerary", []))

        if new_days < current_days:
            plan["itinerary"] = plan["itinerary"][:new_days]
            if plan["itinerary"]:
                plan["itinerary"][-1]["title"] = f"Despedida de {plan['destination']}"
        elif new_days > current_days and current_days > 0:
            for d in range(current_days + 1, new_days + 1):
                plan["itinerary"].append({
                    "day": d,
                    "title": f"Dia {d}: Explorar {plan['destination']}",
                    "activities": ["Dia livre para explorar ao teu ritmo", "Visita zonas menos turisticas", "Descansa e aproveita a cidade"],
                })

        for i, day in enumerate(plan.get("itinerary", [])):
            day["day"] = i + 1

        # Update must_see for new duration
        if "must_see" in plan and isinstance(plan["must_see"], list):
            max_sights = max(3, min(new_days * 2, len(plan["must_see"])))
            plan["must_see"] = plan["must_see"][:max_sights]
    except ValueError:
        pass

    return plan
