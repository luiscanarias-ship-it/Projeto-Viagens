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
    """Build a deterministic itinerary — NEVER repeats activities, distributes evenly."""
    attractions = dest_data.get("attractions", {})
    iconic = list(attractions.get("iconic", []))
    cultural = list(attractions.get("cultural", []))
    local = list(attractions.get("local", []))
    food = list(attractions.get("food", []))
    day_trips = list(dest_data.get("day_trips", []))
    stay_zones = dest_data.get("stay_zones", [])

    used = set()

    def pick(pool, count=1):
        result = []
        for item in pool:
            if item not in used and len(result) < count:
                result.append(item)
                used.add(item)
        return result

    itinerary = []

    # Day 1: Arrival + 1 iconic + 1 local + 1 food
    day1 = [f"Chegada e check-in no hotel ({dest_data.get('hotel_area', 'centro')})"]
    day1 += pick(iconic, 1)
    day1 += pick(local, 1)
    day1 += pick(food, 1)
    itinerary.append({"day": 1, "title": f"Chegada a {dest_data['name']}", "activities": day1[:4]})

    # Middle days: 1 from each main category + 1 food = 4 per day (even distribution)
    day_themes = [
        f"Icones de {dest_data['name']}",
        "Cultura e descobertas",
        f"Bairros e sabores de {dest_data['name']}",
        f"Arte e historia de {dest_data['name']}",
        f"O lado local de {dest_data['name']}",
    ]
    pools_order = [
        ["iconic", "cultural", "local"],
        ["cultural", "local", "iconic"],
        ["local", "iconic", "cultural"],
        ["iconic", "cultural", "local"],
        ["cultural", "local", "iconic"],
    ]
    pools_map = {"iconic": iconic, "cultural": cultural, "local": local, "food": food}

    for d in range(2, num_days):
        theme_idx = (d - 2) % len(day_themes)
        title = day_themes[theme_idx]
        cats = pools_order[theme_idx]

        acts = []
        # Pick 1 from each main category
        for cat in cats:
            acts += pick(pools_map[cat], 1)
        # Always add a food experience
        acts += pick(food, 1)

        # If less than 3 activities, supplement with day trips
        if len(acts) < 3 and day_trips:
            trips = pick(day_trips, min(2, 3 - len(acts)))
            acts += trips
            if trips and len(acts) <= len(trips) + 1:
                trip_name = trips[0].split('—')[0].replace('Day trip ', '').replace('a ', '').strip()
                title = f"Excursao: {trip_name}"

        # If STILL less than 3, add zone-based exploration
        if len(acts) < 3:
            for zi in range(len(stay_zones)):
                zone = stay_zones[(d - 2 + zi) % len(stay_zones)]
                fillers = [
                    f"Explorar a zona de {zone['name']} — {zone.get('vibe', 'bairro local')}",
                    f"Passeio matinal e cafe local no bairro de {zone['name']}",
                ]
                for filler in fillers:
                    if filler not in used and len(acts) < 4:
                        acts.append(filler)
                        used.add(filler)
                if len(acts) >= 3:
                    break
            if len(acts) < 3:
                filler = f"Tempo livre para explorar {dest_data['name']} ao teu ritmo"
                if filler not in used:
                    acts.append(filler)
                    used.add(filler)

        itinerary.append({"day": d, "title": title, "activities": acts[:4]})

    # Last day: departure
    last = ["Check-out do hotel"]
    leftover_local = pick(local, 1)
    if leftover_local:
        last.append(f"Ultima visita: {leftover_local[0].split('(')[0].strip()}")
    else:
        last.append(f"Passeio de despedida pelo centro de {dest_data['name']}")
    leftover_food = pick(food, 1)
    if leftover_food:
        last.append(f"Almoco de despedida: {leftover_food[0]}")
    else:
        last.append(f"Almoco de despedida num restaurante local")
    last.append("Transfer para o aeroporto e regresso")
    itinerary.append({"day": num_days, "title": f"Despedida de {dest_data['name']}", "activities": last[:4]})

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
