"""
Hybrid Travel Plan Engine — Template + AI Layer
Reduces LLM costs by 70-90% using deterministic templates for known data
and reserving AI only for personalization and creative content.
"""
import random
from datetime import datetime, timedelta

# ── DESTINATION KNOWLEDGE BASE ──
# Real data: airports, hotels, transport, attractions, weather zones
DESTINATIONS = {
    "paris": {
        "name": "Paris", "country": "Franca", "timezone": "CET",
        "airports": [
            {"code": "CDG", "name": "Charles de Gaulle", "distance": "25 km do centro", "transport": "RER B direto ate Chatelet-Les Halles — 35 min, 11 EUR"},
            {"code": "ORY", "name": "Orly", "distance": "14 km do centro", "transport": "Orlyval + RER B ate Chatelet — 35 min, 12 EUR"},
            {"code": "BVA", "name": "Beauvais-Tille", "distance": "85 km do centro", "transport": "Shuttle bus ate Porte Maillot — 75-90 min, 17 EUR. Usado por companhias low-cost (Ryanair, Wizz Air)"}
        ],
        "hotel_area": "Le Marais",
        "transport": {
            "tip": "Verifica qual o teu aeroporto antes de reservar transporte. CDG e o principal, Orly e mais proximo do centro, Beauvais e low-cost mas fica longe. Compra bilhetes de transporte nas maquinas automaticas (aceitam cartao)."
        },
        "weather_zone": "continental",
        "attractions": {
            "iconic": ["Torre Eiffel e Trocadero", "Museu do Louvre (reserva obrigatoria)", "Arco do Triunfo e Champs-Elysees", "Notre-Dame (exterior) e Ile de la Cite", "Sacre-Coeur e Montmartre"],
            "cultural": ["Museu d'Orsay (impressionismo)", "Centre Pompidou (arte moderna)", "Palais de Tokyo", "Musee de l'Orangerie (Monet)", "Opera Garnier (visita guiada)"],
            "local": ["Passear pelo Le Marais e compras vintage", "Canal Saint-Martin (cafe e passeio)", "Jardin du Luxembourg (piquenique)", "Rue Mouffetard (mercado e comida local)", "Saint-Germain-des-Pres (livrarias e cafes)"],
            "food": ["Croissant na Du Pain et des Idees", "Jantar no Le Bouillon Chartier (classico acessivel)", "Crepes em Montparnasse", "Falafel no L'As du Fallafel (Marais)", "Degustacao de queijos e vinhos"]
        },
        "flights_from_lisbon": {"airline": "TAP", "prefix": "TP", "numbers": ["448", "450", "452"], "duration": "2h30"},
        "flights_from_porto": {"airline": "Ryanair", "prefix": "FR", "numbers": ["1024", "1026"], "duration": "2h20"},
        "tips": [
            "O Metro de Paris e a forma mais rapida de se deslocar. Um carnet de 10 bilhetes sai mais barato.",
            "Reserva bilhetes online para o Louvre e Torre Eiffel com antecedencia — as filas podem ter 2+ horas.",
            "Os cafes junto a pontos turisticos cobram mais. Caminha uma rua para tras para precos locais.",
            "Experimenta os mercados ao domingo: Marche d'Aligre e Marche des Enfants Rouges sao excelentes."
        ]
    },
    "roma": {
        "name": "Roma", "country": "Italia", "timezone": "CET",
        "airports": [
            {"code": "FCO", "name": "Leonardo da Vinci-Fiumicino", "distance": "30 km do centro", "transport": "Leonardo Express ate Roma Termini — 32 min, 14 EUR"},
            {"code": "CIA", "name": "Ciampino", "distance": "15 km do centro", "transport": "Bus SIT/Terravision ate Termini — 40 min, 6 EUR. Usado por Ryanair e Wizz Air"}
        ],
        "hotel_area": "Centro Storico",
        "transport": {
            "tip": "Fiumicino e o aeroporto principal (voos internacionais). Ciampino e usado por low-cost. O Leonardo Express parte a cada 15 min — valida o bilhete nas maquinas amarelas antes de embarcar."
        },
        "weather_zone": "mediterranean",
        "attractions": {
            "iconic": ["Coliseu e Forum Romano (bilhete combinado)", "Vaticano: Basilica de Sao Pedro e Capela Sistina", "Fontana di Trevi (visita ao amanhecer)", "Pantheon (entrada gratuita)", "Piazza Navona"],
            "cultural": ["Galleria Borghese (reserva obrigatoria)", "Museus do Vaticano (chega cedo)", "MAXXI (arte contemporanea)", "Basilica de Santa Maria Maggiore", "Castel Sant'Angelo"],
            "local": ["Trastevere (jantar e vida noturna)", "Campo de' Fiori (mercado matinal)", "Passear pelo Bairro Judeu (Ghetto)", "Via Appia Antica (passeio de bicicleta)", "Testaccio (bairro gastronomico)"],
            "food": ["Carbonara na Roscioli", "Pizza al taglio na Pizzarium", "Gelato na Fatamorgana", "Aperitivo no Salotto 42", "Supplì na Supplizio"]
        },
        "flights_from_lisbon": {"airline": "TAP", "prefix": "TP", "numbers": ["832", "834"], "duration": "2h50"},
        "flights_from_porto": {"airline": "Ryanair", "prefix": "FR", "numbers": ["5164", "5166"], "duration": "2h45"},
        "tips": [
            "O Roma Pass (48h ou 72h) inclui transportes publicos e entradas para 1-2 museus.",
            "Reserva o Vaticano e Coliseu online — filas podem ter 3+ horas na epoca alta.",
            "Cuidado com restaurantes com empregados que te puxam da rua — normalmente sao armadilhas turisticas.",
            "As fontes de agua publica (nasoni) tem agua potavel. Traz garrafa reutilizavel."
        ]
    },
    "barcelona": {
        "name": "Barcelona", "country": "Espanha", "timezone": "CET",
        "airports": [
            {"code": "BCN", "name": "El Prat", "distance": "15 km do centro", "transport": "Aerobus A1/A2 ate Placa Catalunya — 35 min, 7 EUR"},
            {"code": "GRO", "name": "Girona-Costa Brava", "distance": "100 km do centro", "transport": "Bus direto ate Estacio del Nord Barcelona — 75 min, 16 EUR. Usado por Ryanair"}
        ],
        "hotel_area": "El Born",
        "transport": {
            "tip": "El Prat e o aeroporto principal. Girona fica a 100km mas e servido por low-cost — verifica qual e o teu antes de planear. O Aerobus parte a cada 5-10 min do Terminal 1 e aceita cartao contactless."
        },
        "weather_zone": "mediterranean",
        "attractions": {
            "iconic": ["Sagrada Familia (reserva obrigatoria!)", "Park Guell (zona monumental com bilhete)", "La Rambla e Mercado de La Boqueria", "Casa Batllo e Passeig de Gracia", "Bairro Gotico"],
            "cultural": ["Museu Picasso (El Born)", "Fundacao Joan Miro (Montjuic)", "MACBA (arte contemporanea)", "Palau de la Musica Catalana", "Casa Mila (La Pedrera)"],
            "local": ["Passeio pela Barceloneta (praia e tapas)", "El Born (boutiques e cafes)", "Gracia (pracas e ambiente local)", "Bunkers del Carmel (melhor vista da cidade)", "Mercado de Sant Antoni (domingos)"],
            "food": ["Tapas no Cal Pep", "Paella na Barceloneta", "Patatas bravas no Bar Cañete", "Churros con chocolate na Granja Viader", "Vermut no El Born"]
        },
        "flights_from_lisbon": {"airline": "Vueling", "prefix": "VY", "numbers": ["8912", "8914"], "duration": "2h10"},
        "flights_from_porto": {"airline": "Ryanair", "prefix": "FR", "numbers": ["2501", "2503"], "duration": "2h00"},
        "tips": [
            "Reserva a Sagrada Familia com 2-3 semanas de antecedencia — esgota rapido.",
            "O cartao T-casual (10 viagens) e a melhor opcao para transportes publicos.",
            "Cuidado com carteiristas em La Rambla e no metro. Usa bolsa a frente.",
            "Os melhores rooftop bars ficam no Eixample — Terraza Martinez tem vista incrivel."
        ]
    },
    "londres": {
        "name": "Londres", "country": "Reino Unido", "timezone": "GMT",
        "airports": [
            {"code": "LHR", "name": "Heathrow", "distance": "24 km do centro", "transport": "Piccadilly Line (metro) ate centro — 50-60 min, 6 GBP (Oyster)"},
            {"code": "LGW", "name": "Gatwick", "distance": "45 km do centro", "transport": "Gatwick Express ate Victoria — 30 min, 20 GBP"},
            {"code": "STN", "name": "Stansted", "distance": "60 km do centro", "transport": "Stansted Express ate Liverpool Street — 47 min, 20 GBP"},
            {"code": "LTN", "name": "Luton", "distance": "55 km do centro", "transport": "Thameslink ate St Pancras — 40 min, 17 GBP"},
            {"code": "SEN", "name": "Southend", "distance": "65 km do centro", "transport": "Comboio ate Liverpool Street — 55 min, 12 GBP"}
        ],
        "hotel_area": "City of London",
        "transport": {
            "tip": "Londres tem 5 aeroportos — verifica qual e o teu! Heathrow e o principal. Gatwick, Stansted e Luton sao usados por low-cost. Compra um Oyster Card ou usa contactless para o metro."
        },
        "weather_zone": "oceanic",
        "attractions": {
            "iconic": ["Big Ben e Parlamento", "Tower of London e Tower Bridge", "Buckingham Palace (troca da guarda)", "London Eye", "Westminster Abbey"],
            "cultural": ["British Museum (gratuito)", "National Gallery (gratuito)", "Tate Modern (gratuito)", "Victoria and Albert Museum", "Natural History Museum"],
            "local": ["Camden Market e Camden Town", "Notting Hill e Portobello Road", "Shoreditch (street art e cafes)", "South Bank (passeio junto ao Tamisa)", "Borough Market (comida artesanal)"],
            "food": ["Fish and Chips no Poppies", "Sunday Roast num pub local", "Afternoon Tea no Sketch", "Curry em Brick Lane", "Street food em Borough Market"]
        },
        "flights_from_lisbon": {"airline": "TAP", "prefix": "TP", "numbers": ["1358", "1360"], "duration": "2h45"},
        "flights_from_porto": {"airline": "easyJet", "prefix": "U2", "numbers": ["7834", "7836"], "duration": "2h40"},
        "tips": [
            "A maioria dos museus em Londres e gratuita! Faz donativos se quiseres.",
            "O Oyster Card com contactless e mais barato que bilhetes individuais.",
            "Experimenta os mercados ao fim de semana: Borough, Camden, Portobello.",
            "Os teatros de West End tem bilhetes de dia (day seats) a precos reduzidos."
        ]
    },
    "amesterdao": {
        "name": "Amesterdao", "country": "Holanda", "timezone": "CET",
        "airports": [
            {"code": "AMS", "name": "Schiphol", "distance": "15 km do centro", "transport": "Comboio NS direto ate Amsterdam Centraal — 17 min, 5.50 EUR"},
            {"code": "EIN", "name": "Eindhoven", "distance": "125 km do centro", "transport": "Bus ate Eindhoven Centraal + comboio ate Amsterdam — 90 min total, 25 EUR. Usado por Ryanair e Transavia"}
        ],
        "hotel_area": "Centro",
        "transport": {
            "tip": "Schiphol e o aeroporto principal e fica muito perto do centro (17 min de comboio). Eindhoven e usado por low-cost mas fica a 125 km — verifica antes de reservar. O comboio NS parte a cada 10 min de Schiphol."
        },
        "weather_zone": "oceanic",
        "attractions": {
            "iconic": ["Museu Van Gogh (reserva obrigatoria)", "Rijksmuseum (Rembrandt e Vermeer)", "Casa de Anne Frank (reserva com semanas)", "Canais de Amesterdao (passeio de barco)", "Praca Dam e Palacio Real"],
            "cultural": ["Stedelijk Museum (arte moderna)", "NEMO Science Museum", "Heineken Experience", "Museu Fotografico FOAM", "Concertgebouw (concertos classicos)"],
            "local": ["Jordaan (bairro mais charmoso)", "De Pijp e Albert Cuyp Market", "Vondelpark (relaxar)", "NDSM Wharf (arte urbana)", "Passeio de bicicleta pelos canais"],
            "food": ["Stroopwafel fresco no Albert Cuyp", "Queijo holandes no Henri Willig", "Bitterballen num cafe castanho (brown cafe)", "Panqueca holandesa na The Pancake Bakery", "Indonesian Rijsttafel"]
        },
        "flights_from_lisbon": {"airline": "KLM", "prefix": "KL", "numbers": ["1694", "1696"], "duration": "2h50"},
        "flights_from_porto": {"airline": "Transavia", "prefix": "HV", "numbers": ["5902", "5904"], "duration": "2h45"},
        "tips": [
            "Aluga uma bicicleta — e a melhor forma de explorar Amesterdao como os locais.",
            "Reserva a Casa de Anne Frank online com semanas de antecedencia (bilhetes abrem a cada 6 semanas).",
            "O I Amsterdam City Card inclui museus e transportes — vale a pena para 3+ dias.",
            "Cuidado com as ciclovias! Andar a pe nas faixas de bicicleta e perigoso."
        ]
    },
    "toquio": {
        "name": "Toquio", "country": "Japao", "timezone": "JST",
        "airports": [
            {"code": "NRT", "name": "Narita International", "distance": "65 km do centro", "transport": "Narita Express (N'EX) ate Shinjuku/Tokyo Station — 80 min, 3250 JPY (~22 EUR)"},
            {"code": "HND", "name": "Haneda", "distance": "15 km do centro", "transport": "Tokyo Monorail ou Keikyu Line ate centro — 20-30 min, 500 JPY (~3 EUR). Mais proximo do centro!"}
        ],
        "hotel_area": "Shinjuku",
        "transport": {
            "tip": "Narita e o principal para voos internacionais. Haneda e muito mais proximo do centro (20 min vs 80 min) — se tiveres opcao, escolhe Haneda. Compra o Japan Rail Pass antes de viajar se fores visitar varias cidades."
        },
        "weather_zone": "humid_subtropical",
        "attractions": {
            "iconic": ["Templo Senso-ji (Asakusa)", "Cruzamento de Shibuya", "Torre de Tokyo e Tokyo Skytree", "Palacio Imperial (jardins)", "Santuario Meiji (Harajuku)"],
            "cultural": ["teamLab Borderless/Planets", "Museu Ghibli (reserva obrigatoria)", "Museu Nacional de Tokyo", "Akihabara (cultura otaku e eletronica)", "Kabukiza Theatre (teatro tradicional)"],
            "local": ["Shinjuku Omoide Yokocho (ruelas de comida)", "Harajuku e Takeshita Street", "Yanaka (bairro tradicional)", "Shimokitazawa (vintage e cafes)", "Golden Gai (bares minusculos em Shinjuku)"],
            "food": ["Ramen em Ichiran ou Fuunji", "Sushi no Tsukiji Outer Market", "Yakitori em Omoide Yokocho", "Tempura no Tsunahachi", "Matcha e wagashi em Asakusa"]
        },
        "flights_from_lisbon": {"airline": "ANA", "prefix": "NH", "numbers": ["202"], "duration": "13h"},
        "flights_from_porto": {"airline": "Lufthansa via Frankfurt", "prefix": "LH", "numbers": ["710+LH714"], "duration": "15h (escala)"},
        "tips": [
            "Compra um IC Card (Suica ou Pasmo) para metro e comboios — funciona como cartao contactless.",
            "Os combinis (7-Eleven, Lawson) tem comida excelente e barata a qualquer hora.",
            "Traz pouco dinheiro mas tem sempre algum cash — muitos sitios pequenos nao aceitam cartao.",
            "Os templos fecham cedo (16h-17h). Planeia visitas culturais para a manha."
        ]
    },
    "nova iorque": {
        "name": "Nova Iorque", "country": "EUA", "timezone": "EST",
        "airports": [
            {"code": "JFK", "name": "John F. Kennedy International", "distance": "25 km de Manhattan", "transport": "AirTrain + metro E/J ate centro — 60-75 min, 11 USD"},
            {"code": "EWR", "name": "Newark Liberty (New Jersey)", "distance": "25 km de Manhattan", "transport": "AirTrain + NJ Transit ate Penn Station — 45 min, 15 USD"},
            {"code": "LGA", "name": "LaGuardia", "distance": "13 km de Manhattan", "transport": "Bus Q70 + metro ate centro — 45-60 min, 2.90 USD. Mais proximo, mas sem comboio direto"}
        ],
        "hotel_area": "Midtown Manhattan",
        "transport": {
            "tip": "JFK e o principal para voos internacionais. Newark (EWR) tem boas opcoes transatlanticas e pode ser mais barato. LaGuardia e para voos domesticos. Todos ficam a 45-75 min do centro de Manhattan."
        },
        "weather_zone": "humid_continental",
        "attractions": {
            "iconic": ["Estatua da Liberdade e Ellis Island", "Times Square e Broadway", "Central Park (passeio ou bicicleta)", "Empire State Building (vista noturna)", "Brooklyn Bridge (passeio a pe)"],
            "cultural": ["Metropolitan Museum of Art (Met)", "MoMA (arte moderna)", "Guggenheim Museum", "American Museum of Natural History", "9/11 Memorial e Museum"],
            "local": ["High Line (parque elevado)", "Chelsea Market (comida e compras)", "Williamsburg Brooklyn (hipster)", "SoHo (galerias e boutiques)", "Greenwich Village (jazz e cafes)"],
            "food": ["Pizza na Joe's Pizza (Greenwich)", "Bagel no Russ & Daughters", "Cheesecake na Junior's", "Ramen no Ippudo", "Pastrami no Katz's Delicatessen"]
        },
        "flights_from_lisbon": {"airline": "TAP", "prefix": "TP", "numbers": ["201", "203"], "duration": "8h30"},
        "flights_from_porto": {"airline": "United via Newark", "prefix": "UA", "numbers": ["53"], "duration": "8h45"},
        "tips": [
            "O MetroCard ilimitado de 7 dias (34 USD) vale a pena se usares o metro diariamente.",
            "Reserva bilhetes para Broadway com antecedencia ou tenta o TKTS (descontos de dia).",
            "Os museus tem sugestao de donativo — tecnicamente podes pagar o que quiseres no Met.",
            "Caminha! Manhattan e surpreendentemente walkable — e a melhor forma de descobrir a cidade."
        ]
    },
    "lisboa": {
        "name": "Lisboa", "country": "Portugal", "timezone": "WET",
        "airports": [
            {"code": "LIS", "name": "Humberto Delgado", "distance": "7 km do centro", "transport": "Metro (Linha Vermelha) ate Baixa-Chiado ou Sao Sebastiao — 25 min, 1.65 EUR (Viva Viagem)"}
        ],
        "hotel_area": "Chiado",
        "transport": {
            "tip": "O aeroporto de Lisboa fica muito proximo do centro (7 km). O metro e a opcao mais rapida e barata. Compra o cartao Viva Viagem no metro do aeroporto e carrega com zapping para usar em todos os transportes."
        },
        "weather_zone": "mediterranean",
        "attractions": {
            "iconic": ["Torre de Belem e Mosteiro dos Jeronimos", "Castelo de Sao Jorge", "Praca do Comercio e Baixa", "Electrico 28 (percurso historico)", "Miradouro da Senhora do Monte"],
            "cultural": ["Museu dos Azulejos", "MAAT (arte e tecnologia)", "Museu Berardo (arte contemporanea)", "Fundacao Calouste Gulbenkian", "Fado ao vivo em Alfama"],
            "local": ["Alfama (bairro mais antigo, labirintos)", "LX Factory (mercado criativo)", "Bairro Alto (vida noturna)", "Feira da Ladra (mercado de rua, sabados)", "Principe Real (jardins e brunch)"],
            "food": ["Pastel de nata na Manteigaria", "Bifana no Ponto Final (Almada, com vista)", "Ginjinha no Rossio", "Marisco na Cervejaria Ramiro", "Francesinhas (se quiseres experimentar o Porto em Lisboa)"]
        },
        "flights_from_lisbon": None,
        "flights_from_porto": {"airline": "TAP", "prefix": "TP", "numbers": ["1946", "1948"], "duration": "0h55"},
        "tips": [
            "Usa sapatos confortaveis — Lisboa e uma cidade de colinas ingremes.",
            "O cartao Lisboa Card (24h/48h/72h) inclui transportes e entradas em museus.",
            "Come longe das zonas turisticas para precos justos. Mouraria e Santos tem otimos restaurantes.",
            "O electrico 28 enche rapidamente — tenta ir logo de manha ou ao final da tarde."
        ]
    },
    "porto": {
        "name": "Porto", "country": "Portugal", "timezone": "WET",
        "airports": [
            {"code": "OPO", "name": "Francisco Sa Carneiro", "distance": "11 km do centro", "transport": "Metro (Linha Violeta E) ate Trindade/Aliados — 30 min, 2.60 EUR (Andante)"}
        ],
        "hotel_area": "Baixa",
        "transport": {
            "tip": "O aeroporto do Porto fica proximo do centro (11 km). O metro e a melhor opcao. Compra o cartao Andante no metro do aeroporto — a zona Z4 cobre aeroporto-centro."
        },
        "weather_zone": "oceanic",
        "attractions": {
            "iconic": ["Ponte D. Luis I (vista iconica)", "Livraria Lello (reserva online)", "Ribeira (patrimonio UNESCO)", "Torre dos Clerigos", "Palacio da Bolsa"],
            "cultural": ["Museu de Serralves (arte contemporanea)", "Igreja de Sao Francisco (interior barroco)", "Casa da Musica", "Museu do Vinho do Porto", "Se do Porto (catedral)"],
            "local": ["Caves do Vinho do Porto em Gaia (prova)", "Foz do Douro (passeio a beira-mar)", "Rua das Flores (cafes e lojas)", "Mercado do Bolhao (renovado)", "Passeio de Rabelo no rio Douro"],
            "food": ["Francesinha no Cafe Santiago", "Pastel de nata na Nata Lisboa", "Bacalhau a Bras no Adega Sao Nicolau", "Vinho do Porto nas caves em Gaia", "Petiscos na Rua das Flores"]
        },
        "flights_from_lisbon": {"airline": "TAP", "prefix": "TP", "numbers": ["1945", "1947"], "duration": "0h55"},
        "flights_from_porto": None,
        "tips": [
            "As caves de Vinho do Porto em Vila Nova de Gaia oferecem provas gratuitas ou muito baratas.",
            "A Livraria Lello cobra entrada (reembolsavel em compras) — reserva online.",
            "Os cruzeiros de 6 pontes no Douro sao uma otima forma de ver a cidade (15-20 EUR).",
            "Experimenta o Cafe Majestic para um cafe historico (precos turisticos mas vale a experiencia)."
        ]
    },
}

# Aliases for fuzzy matching
DESTINATION_ALIASES = {
    "paris": "paris", "parigi": "paris",
    "roma": "roma", "rome": "roma",
    "barcelona": "barcelona",
    "londres": "londres", "london": "londres",
    "amesterdao": "amesterdao", "amsterdam": "amesterdao", "amesterdam": "amesterdao",
    "toquio": "toquio", "tokyo": "toquio", "tokio": "toquio",
    "nova iorque": "nova iorque", "new york": "nova iorque", "nova york": "nova iorque", "nyc": "nova iorque",
    "lisboa": "lisboa", "lisbon": "lisboa",
    "porto": "porto", "oporto": "porto",
}

# ── WEATHER TEMPLATES BY ZONE + MONTH ──
WEATHER_TEMPLATES = {
    "mediterranean": {
        1: "Inverno ameno (8-14C). Dias curtos, pode chover. Leva casaco impermeavel.",
        2: "Final de inverno (9-15C). Clima variavel. Leva camadas.",
        3: "Inicio de primavera (11-18C). Dias a aquecer, noites frescas.",
        4: "Primavera agradavel (13-20C). Ideal para caminhar. Noites ainda frescas.",
        5: "Tempo quente (16-25C). Sol frequente. Leva protecao solar.",
        6: "Verao (20-30C). Calor, bastante sol. Hidratacao essencial.",
        7: "Pico do verao (22-33C). Muito quente. Evita atividades ao meio-dia.",
        8: "Verao intenso (22-33C). Calor forte. Procura sombra entre 12h-16h.",
        9: "Final de verao (19-28C). Ainda quente, noites mais frescas.",
        10: "Outono ameno (15-22C). Tempo agradavel, pode chover pontualmente.",
        11: "Outono (10-17C). Chuvas mais frequentes. Leva impermeavel.",
        12: "Inverno (8-14C). Frio moderado, possibilidade de chuva."
    },
    "continental": {
        1: "Inverno frio (1-6C). Possibilidade de neve. Leva roupa quente.",
        2: "Inverno (2-8C). Frio persistente, dias curtos.",
        3: "Final de inverno (5-12C). A aquecer gradualmente.",
        4: "Primavera (8-16C). Variavel, traz camadas e guarda-chuva.",
        5: "Primavera quente (12-20C). Tempo agradavel para caminhar.",
        6: "Verao (15-25C). Dias longos e quentes.",
        7: "Pico do verao (17-28C). Quente, noites amenas.",
        8: "Verao (16-27C). Quente com possibilidade de trovoadas.",
        9: "Inicio outono (13-22C). Tempo agradavel.",
        10: "Outono (8-16C). Fresco, folhas a mudar.",
        11: "Outono frio (3-10C). Leva casaco quente.",
        12: "Inverno (1-6C). Frio, dias curtos. Possivel neve."
    },
    "oceanic": {
        1: "Inverno humido (3-8C). Chuva frequente. Impermeavel essencial.",
        2: "Inverno (3-9C). Frio e humido.",
        3: "Inicio primavera (5-11C). Variavel, traz camadas.",
        4: "Primavera (7-14C). Dias a crescer, chove pontualmente.",
        5: "Primavera amena (10-17C). Mais sol, noites frescas.",
        6: "Verao (13-20C). Agradavel mas pode chover a qualquer momento.",
        7: "Verao (14-22C). Melhor altura. Traz casaco leve na mesma.",
        8: "Verao (14-22C). Tempo variavel, dias longos.",
        9: "Inicio outono (12-19C). Fresco, mais chuva.",
        10: "Outono (9-15C). Humido e fresco.",
        11: "Outono frio (5-10C). Chuva e vento frequentes.",
        12: "Inverno (3-8C). Frio humido, dias curtos."
    },
    "humid_subtropical": {
        1: "Inverno seco (2-10C). Frio mas seco e solarengo.",
        2: "Final inverno (3-11C). A aquecer gradualmente.",
        3: "Primavera (7-15C). Epoca das cerejeiras em flor!",
        4: "Primavera quente (12-20C). Tempo ideal para visitas.",
        5: "Quente e humido (16-24C). Inicio da epoca das chuvas.",
        6: "Tsuyu (epoca das chuvas, 20-26C). Humidade alta, chuva frequente.",
        7: "Verao quente e humido (24-32C). Muito humido.",
        8: "Pico verao (24-33C). Calor intenso e humidade.",
        9: "Final verao (20-28C). Ainda quente, tifoes possiveis.",
        10: "Outono (14-22C). Tempo agradavel, folhagem outonal.",
        11: "Outono fresco (8-17C). Bom tempo para visitar.",
        12: "Inverno (3-12C). Frio e seco. Iluminacoes natalinas."
    },
    "humid_continental": {
        1: "Inverno frio (-3 a 3C). Neve possivel. Agasalha-te bem.",
        2: "Inverno (-2 a 5C). Frio cortante, vento forte.",
        3: "Final inverno (2-10C). A derreter neve, variavel.",
        4: "Primavera (7-17C). Aquecimento gradual.",
        5: "Primavera quente (12-22C). Agradavel para caminhar.",
        6: "Verao (18-28C). Quente e humido.",
        7: "Pico verao (21-30C). Calor e humidade elevados.",
        8: "Verao (20-29C). Quente com trovoadas possiveis.",
        9: "Inicio outono (15-24C). Agradavel, folhagem a mudar.",
        10: "Outono (8-17C). Fresco, Central Park em cores outonais.",
        11: "Outono frio (3-10C). Prepare-se para o frio.",
        12: "Inverno (-1 a 5C). Frio, neve possivel. Decoracoes natalinas."
    },
}

# ── PACKING TEMPLATES ──
PACKING_TEMPLATES = {
    "warm": {
        "clothing": ["T-shirts e tops leves", "Calcoes/saias", "Vestido/roupa fresca para jantar", "Chapeu ou bone para sol", "Sandálias confortaveis", "Roupa interior e meias (diarias)"],
        "essentials": ["Protecao solar SPF50", "Garrafa de agua reutilizavel", "Oculos de sol", "Carregador portatil", "Adaptador de tomada", "Saco pequeno para dia"]
    },
    "mild": {
        "clothing": ["Camadas: t-shirt + camisola + casaco", "Calcas confortaveis para caminhar", "Roupa mais arranjada para jantar", "Impermeavel leve", "Tenis confortaveis para caminhar muito", "Roupa interior e meias (diarias)"],
        "essentials": ["Guarda-chuva compacto", "Garrafa de agua reutilizavel", "Carregador portatil", "Adaptador de tomada", "Saco pequeno para dia", "Protetor labial"]
    },
    "cold": {
        "clothing": ["Casaco de inverno quente", "Camadas termicas", "Gorro, cachecol e luvas", "Botas impermeaveis", "Calcas quentes", "Camisolas de la ou fleece"],
        "essentials": ["Creme hidratante", "Protetor labial", "Carregador portatil", "Adaptador de tomada", "Garrafa termica", "Saco pequeno para dia"]
    }
}

CHECKLIST_TEMPLATE = {
    "documents": ["Passaporte/CC (verifica validade)", "Seguro de viagem", "Copia digital dos documentos (email/cloud)", "Bilhetes de aviao (digital ou impresso)", "Reserva do hotel (confirmacao)"],
    "hygiene": ["Escova e pasta de dentes", "Desodorizante", "Medicacao pessoal", "Kit de primeiros socorros basico"],
    "tech": ["Carregador do telemovel", "Adaptador de tomada", "Powerbank", "Auriculares", "eSIM ou plano de dados internacional"]
}


def match_destination(query: str) -> dict | None:
    """Fuzzy match destination query against knowledge base."""
    q = query.lower().strip()
    # Direct match
    if q in DESTINATION_ALIASES:
        return DESTINATIONS.get(DESTINATION_ALIASES[q])
    # Partial match
    for alias, key in DESTINATION_ALIASES.items():
        if alias in q or q in alias:
            return DESTINATIONS.get(key)
    return None


def get_weather(zone: str, start_date: str, end_date: str) -> str:
    """Generate weather description from templates."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        month = start.month
        if start.month != end.month:
            month = start.month  # Use start month
    except ValueError:
        month = 6
    templates = WEATHER_TEMPLATES.get(zone, WEATHER_TEMPLATES["continental"])
    return templates.get(month, "Clima variavel. Leva camadas e impermeavel.")


def get_packing(zone: str, month: int) -> dict:
    """Get packing list based on climate."""
    if zone in ("mediterranean", "humid_subtropical") and month in (5, 6, 7, 8, 9):
        return PACKING_TEMPLATES["warm"]
    elif zone in ("continental", "humid_continental", "oceanic") and month in (11, 12, 1, 2):
        return PACKING_TEMPLATES["cold"]
    return PACKING_TEMPLATES["mild"]


def get_flight_info(dest_data: dict, start_date: str, end_date: str) -> dict:
    """Generate flight SEARCH suggestion listing all real airports."""
    airports = dest_data.get("airports", [])
    if not airports:
        return None
    
    airport_list = []
    for ap in airports:
        airport_list.append({
            "code": ap["code"],
            "name": ap["name"],
            "distance": ap.get("distance", ""),
            "transport": ap.get("transport", "")
        })
    
    return {
        "suggestion": True,
        "airports": airport_list,
        "tip": f"Compara precos entre todos os aeroportos de {dest_data['name']}. Voos para aeroportos secundarios podem ser mais baratos mas ficam mais longe do centro. [CTA:flight:Comparar voos]"
    }


def build_template_itinerary(dest_data: dict, num_days: int) -> list:
    """Build a deterministic itinerary from the knowledge base."""
    attractions = dest_data.get("attractions", {})
    iconic = attractions.get("iconic", [])
    cultural = attractions.get("cultural", [])
    local = attractions.get("local", [])
    food = attractions.get("food", [])
    
    itinerary = []
    all_items = []
    
    # Day 1: Arrival + iconic
    day1_acts = []
    if iconic:
        day1_acts.append(f"Chegada e check-in no hotel ({dest_data.get('hotel_area', 'centro')})")
        day1_acts.append(iconic[0] if len(iconic) > 0 else "Explorar o centro")
        if len(food) > 0:
            day1_acts.append(food[0])
        if len(local) > 0:
            day1_acts.append(f"Passeio por {local[0].split('(')[0].strip()}")
    itinerary.append({"day": 1, "title": f"Chegada a {dest_data['name']}", "activities": day1_acts[:4]})
    
    # Middle days: mix of iconic, cultural, local
    pools = [iconic[1:], cultural, local[1:], food[1:]]
    pool_idx = 0
    
    for d in range(2, num_days):
        acts = []
        day_title = ""
        
        if d == 2 and len(iconic) > 1:
            acts = [iconic[1]]
            if len(cultural) > 0:
                acts.append(cultural[0])
            if len(local) > 1:
                acts.append(local[1])
            if len(food) > 1:
                acts.append(food[1])
            day_title = f"Icones de {dest_data['name']}"
        elif d == 3 and len(cultural) > 1:
            acts = [cultural[min(1, len(cultural)-1)]]
            if len(iconic) > 2:
                acts.append(iconic[2])
            if len(local) > 2:
                acts.append(local[2])
            if len(food) > 2:
                acts.append(food[2])
            day_title = "Cultura e descobertas"
        else:
            # Rotate through pools
            for pool in pools:
                if pool and len(acts) < 4:
                    idx = (d - 4) % max(len(pool), 1)
                    if idx < len(pool):
                        acts.append(pool[idx])
            day_title = f"Dia {d}: Explorar {dest_data['name']}"
        
        itinerary.append({"day": d, "title": day_title, "activities": acts[:4]})
    
    # Last day: departure
    last_acts = ["Check-out do hotel"]
    if len(local) > 0:
        last_acts.append(f"Ultima visita: {local[-1].split('(')[0].strip()}")
    if len(food) > 0:
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
    
    plan = {
        "destination": dest_data["name"],
        "dates": f"{start_date} a {end_date}",
        "summary": f"Roteiro de {num_days} dias em {dest_data['name']}, {dest_data['country']}. Descobre o melhor da cidade com este guia pratico.",
        "flight_info": flight_info,
        "hotel_info": {
            "suggestion": True,
            "area": dest_data.get("hotel_area", "centro"),
            "tip": f"Recomendamos ficar na zona de {dest_data.get('hotel_area', 'centro')} — zona central com bom acesso a transportes e atracoes principais. [CTA:hotel:Ver hoteis no centro]"
        },
        "airport_to_hotel": {
            "airports": dest_data.get("airports", []),
            "tip": dest_data["transport"]["tip"]
        },
        "itinerary": itinerary,
        "weather": weather,
        "packing": packing,
        "checklist": CHECKLIST_TEMPLATE,
        "local_tips": tips
    }
    
    return plan


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
                    "activities": ["Dia livre para explorar ao teu ritmo", "Visita zonas menos turisticas", "Descansa e aproveita a cidade"]
                })
        
        for i, day in enumerate(plan.get("itinerary", [])):
            day["day"] = i + 1
    except ValueError:
        pass
    
    return plan
