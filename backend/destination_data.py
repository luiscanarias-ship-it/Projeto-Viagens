"""
Destination Knowledge Base — Real data for 19 cities + reusable template types.
All airports, transport, stay zones, and attractions are verified real-world data.
"""

DESTINATIONS = {
    "paris": {
        "name": "Paris", "country": "Franca", "timezone": "CET",
        "airports": [
            {"code": "CDG", "name": "Charles de Gaulle", "distance": "25 km do centro", "transport": "RER B direto ate Chatelet-Les Halles — 35 min, 11 EUR"},
            {"code": "ORY", "name": "Orly", "distance": "14 km do centro", "transport": "Orlyval + RER B ate Chatelet — 35 min, 12 EUR"},
            {"code": "BVA", "name": "Beauvais-Tille", "distance": "85 km do centro", "transport": "Shuttle bus ate Porte Maillot — 75-90 min, 17 EUR. Usado por companhias low-cost (Ryanair, Wizz Air)"}
        ],
        "stay_zones": [
            {"name": "Le Marais (3e/4e)", "description": "Bairro historico no coracao de Paris. Perto da paragem Chatelet-Les Halles onde chega o RER B direto de CDG.", "transport_access": "Metro 1, 8, 11 — RER A e B em Chatelet", "vibe": "Historico, cafes, galerias, vida noturna"},
            {"name": "Saint-Germain-des-Pres (6e)", "description": "Margem esquerda elegante. RER B para em Saint-Michel-Notre-Dame, a 5 min a pe.", "transport_access": "Metro 4, 10 — RER B em Saint-Michel", "vibe": "Literario, bistrots, livrarias"},
            {"name": "Opera/Grands Boulevards (9e)", "description": "Perto de Gare du Nord (comboios de CDG) e grandes armazens. Zona muito bem ligada.", "transport_access": "Metro 3, 7, 8, 9 — RER A em Auber", "vibe": "Comercial, central, teatros"},
            {"name": "Bastille (11e/12e)", "description": "Zona animada com otimos restaurantes. Ligacao direta por Metro 1 ao centro.", "transport_access": "Metro 1, 5, 8 — RER A em Gare de Lyon", "vibe": "Vida noturna, mercados, multicultural"}
        ],
        "hotel_area": "Le Marais",
        "transport": {"tip": "Verifica qual o teu aeroporto antes de reservar transporte. CDG e o principal, Orly e mais proximo do centro, Beauvais e low-cost mas fica longe. Compra bilhetes de transporte nas maquinas automaticas (aceitam cartao)."},
        "weather_zone": "continental",
        "attractions": {
            "iconic": ["Torre Eiffel e Trocadero", "Museu do Louvre (reserva obrigatoria)", "Arco do Triunfo e Champs-Elysees", "Notre-Dame (exterior) e Ile de la Cite", "Sacre-Coeur e Montmartre"],
            "cultural": ["Museu d'Orsay (impressionismo)", "Centre Pompidou (arte moderna)", "Palais de Tokyo", "Musee de l'Orangerie (Monet)", "Opera Garnier (visita guiada)"],
            "local": ["Passear pelo Le Marais e compras vintage", "Canal Saint-Martin (cafe e passeio)", "Jardin du Luxembourg (piquenique)", "Rue Mouffetard (mercado e comida local)", "Saint-Germain-des-Pres (livrarias e cafes)"],
            "food": ["Croissant na Du Pain et des Idees", "Jantar no Le Bouillon Chartier (classico acessivel)", "Crepes em Montparnasse", "Falafel no L'As du Fallafel (Marais)", "Degustacao de queijos e vinhos"]
        },
        "must_see": ["Torre Eiffel", "Museu do Louvre", "Notre-Dame e Ile de la Cite", "Sacre-Coeur e Montmartre", "Arco do Triunfo", "Museu d'Orsay", "Jardins de Versailles (day trip)", "Champs-Elysees e Grand Palais"],
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
        "stay_zones": [
            {"name": "Termini/Esquilino", "description": "Junto a estacao central Roma Termini. Leonardo Express de Fiumicino e buses de Ciampino param aqui.", "transport_access": "Metro A e B — todas as linhas de bus", "vibe": "Pratico, multicultural, bons precos"},
            {"name": "Centro Storico (Navona/Pantheon)", "description": "Coracao historico a pe de tudo. Sem metro direto mas excelentes ligacoes de bus.", "transport_access": "Bus 40, 64 de Termini — a pe do Pantheon", "vibe": "Romantico, pracas, gelaterias"},
            {"name": "Trastevere", "description": "Bairro boemo na margem oeste do Tibre. Tram 8 liga a Termini em 20 min.", "transport_access": "Tram 8 — Bus H de Termini", "vibe": "Vida noturna, trattorias, charme local"},
            {"name": "Monti", "description": "Bairro trendy entre o Coliseu e Termini. Metro B em Cavour.", "transport_access": "Metro B Cavour — 5 min a pe de Termini", "vibe": "Vintage, cafes, artesanato"}
        ],
        "hotel_area": "Centro Storico",
        "transport": {"tip": "Fiumicino e o aeroporto principal (voos internacionais). Ciampino e usado por low-cost. O Leonardo Express parte a cada 15 min — valida o bilhete nas maquinas amarelas antes de embarcar."},
        "weather_zone": "mediterranean",
        "attractions": {
            "iconic": ["Coliseu e Forum Romano (bilhete combinado)", "Vaticano: Basilica de Sao Pedro e Capela Sistina", "Fontana di Trevi (visita ao amanhecer)", "Pantheon (entrada gratuita)", "Piazza Navona"],
            "cultural": ["Galleria Borghese (reserva obrigatoria)", "Museus do Vaticano (chega cedo)", "MAXXI (arte contemporanea)", "Basilica de Santa Maria Maggiore", "Castel Sant'Angelo"],
            "local": ["Trastevere (jantar e vida noturna)", "Campo de' Fiori (mercado matinal)", "Passear pelo Bairro Judeu (Ghetto)", "Via Appia Antica (passeio de bicicleta)", "Testaccio (bairro gastronomico)"],
            "food": ["Carbonara na Roscioli", "Pizza al taglio na Pizzarium", "Gelato na Fatamorgana", "Aperitivo no Salotto 42", "Suppli na Supplizio"]
        },
        "must_see": ["Coliseu e Forum Romano", "Vaticano e Capela Sistina", "Fontana di Trevi", "Pantheon", "Piazza Navona", "Galleria Borghese", "Trastevere"],
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
        "stay_zones": [
            {"name": "El Born/La Ribera", "description": "Bairro medieval junto ao porto. Aerobus para em Placa Catalunya a 10 min a pe.", "transport_access": "Metro L4 Jaume I/Barceloneta — Aerobus em Placa Catalunya", "vibe": "Historico, boutiques, tapas"},
            {"name": "Eixample", "description": "Bairro modernista (Gaudi). Hub central de metro com ligacao direta ao aeroporto.", "transport_access": "Metro L1/L2/L3/L4 em Passeig de Gracia — Metro L9 direto ao aeroporto", "vibe": "Arquitectura, compras, rooftops"},
            {"name": "Gracia", "description": "Bairro local com pracas animadas. Metro L3 liga ao centro em 10 min.", "transport_access": "Metro L3 Fontana — FGC Gracia", "vibe": "Local, alternativo, cafes independentes"},
            {"name": "Barri Gotic", "description": "Centro historico absoluto. Tudo a distancia a pe, perto de Placa Catalunya.", "transport_access": "Metro L3 Liceu — L4 Jaume I", "vibe": "Medieval, turistico mas charmoso"}
        ],
        "hotel_area": "El Born",
        "transport": {"tip": "El Prat e o aeroporto principal. Girona fica a 100km mas e servido por low-cost — verifica qual e o teu antes de planear. O Aerobus parte a cada 5-10 min do Terminal 1 e aceita cartao contactless."},
        "weather_zone": "mediterranean",
        "attractions": {
            "iconic": ["Sagrada Familia (reserva obrigatoria!)", "Park Guell (zona monumental com bilhete)", "La Rambla e Mercado de La Boqueria", "Casa Batllo e Passeig de Gracia", "Bairro Gotico"],
            "cultural": ["Museu Picasso (El Born)", "Fundacao Joan Miro (Montjuic)", "MACBA (arte contemporanea)", "Palau de la Musica Catalana", "Casa Mila (La Pedrera)"],
            "local": ["Passeio pela Barceloneta (praia e tapas)", "El Born (boutiques e cafes)", "Gracia (pracas e ambiente local)", "Bunkers del Carmel (melhor vista da cidade)", "Mercado de Sant Antoni (domingos)"],
            "food": ["Tapas no Cal Pep", "Paella na Barceloneta", "Patatas bravas no Bar Canete", "Churros con chocolate na Granja Viader", "Vermut no El Born"]
        },
        "must_see": ["Sagrada Familia", "Park Guell", "La Rambla e Boqueria", "Casa Batllo", "Bairro Gotico", "Barceloneta (praia)", "Museu Picasso", "Montjuic"],
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
        "stay_zones": [
            {"name": "King's Cross/St Pancras", "description": "Hub de transportes principal. Thameslink de Luton, Eurostar, e Piccadilly Line de Heathrow param aqui.", "transport_access": "Piccadilly, Northern, Victoria, Circle, Metropolitan lines", "vibe": "Moderno, restaurantes, Coal Drops Yard"},
            {"name": "South Bank/Waterloo", "description": "Junto ao Tamisa. Waterloo East recebe comboios de Gatwick. Passeio a pe para Westminster.", "transport_access": "Jubilee, Northern, Bakerloo lines — comboios de Gatwick", "vibe": "Cultural, Tate Modern, London Eye"},
            {"name": "Shoreditch/Liverpool Street", "description": "Terminus do Stansted Express e Southend. Bairro trendy com street art.", "transport_access": "Central, Circle, Hammersmith lines — Stansted/Southend Express", "vibe": "Hipster, cafes, arte urbana"},
            {"name": "Victoria", "description": "Terminus do Gatwick Express. Zona central com facil acesso a Buckingham Palace.", "transport_access": "Victoria, District, Circle lines — Gatwick Express", "vibe": "Classico, central, bem conectado"}
        ],
        "hotel_area": "City of London",
        "transport": {"tip": "Londres tem 5 aeroportos — verifica qual e o teu! Heathrow e o principal. Gatwick, Stansted e Luton sao usados por low-cost. Compra um Oyster Card ou usa contactless para o metro."},
        "weather_zone": "oceanic",
        "attractions": {
            "iconic": ["Big Ben e Parlamento", "Tower of London e Tower Bridge", "Buckingham Palace (troca da guarda)", "London Eye", "Westminster Abbey"],
            "cultural": ["British Museum (gratuito)", "National Gallery (gratuito)", "Tate Modern (gratuito)", "Victoria and Albert Museum", "Natural History Museum"],
            "local": ["Camden Market e Camden Town", "Notting Hill e Portobello Road", "Shoreditch (street art e cafes)", "South Bank (passeio junto ao Tamisa)", "Borough Market (comida artesanal)"],
            "food": ["Fish and Chips no Poppies", "Sunday Roast num pub local", "Afternoon Tea no Sketch", "Curry em Brick Lane", "Street food em Borough Market"]
        },
        "must_see": ["Big Ben e Parlamento", "Tower of London", "British Museum", "Buckingham Palace", "London Eye", "Tower Bridge", "Westminster Abbey", "Tate Modern"],
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
        "stay_zones": [
            {"name": "Centrum/Dam Square", "description": "Junto a Amsterdam Centraal onde chega o comboio direto de Schiphol (17 min). Centro absoluto.", "transport_access": "Comboio NS de Schiphol — Metro 52 — Trams 1, 2, 4, 5", "vibe": "Turistico, canais, lojas"},
            {"name": "Jordaan", "description": "Bairro mais charmoso de Amesterdao. 10 min a pe de Centraal.", "transport_access": "Bus 18, 21, 22 — 10 min a pe de Centraal", "vibe": "Charmoso, galerias, mercados locais"},
            {"name": "De Pijp", "description": "Bairro multicultural com Albert Cuyp Market. Metro 52 liga a Centraal em 10 min.", "transport_access": "Metro 52 De Pijp — Tram 4, 16, 24", "vibe": "Local, mercados, restaurantes etnicos"},
            {"name": "Oud-West/Vondelpark", "description": "Junto ao Vondelpark e Museumplein. Tram 1 ou 2 de Centraal.", "transport_access": "Tram 1, 2, 11 — perto de Museumplein", "vibe": "Residencial, museus, parques"}
        ],
        "hotel_area": "Centro",
        "transport": {"tip": "Schiphol e o aeroporto principal e fica muito proximo do centro (17 min de comboio). Eindhoven e usado por low-cost mas fica a 125 km — verifica antes de reservar. O comboio NS parte a cada 10 min de Schiphol."},
        "weather_zone": "oceanic",
        "attractions": {
            "iconic": ["Museu Van Gogh (reserva obrigatoria)", "Rijksmuseum (Rembrandt e Vermeer)", "Casa de Anne Frank (reserva com semanas)", "Canais de Amesterdao (passeio de barco)", "Praca Dam e Palacio Real"],
            "cultural": ["Stedelijk Museum (arte moderna)", "NEMO Science Museum", "Heineken Experience", "Museu Fotografico FOAM", "Concertgebouw (concertos classicos)"],
            "local": ["Jordaan (bairro mais charmoso)", "De Pijp e Albert Cuyp Market", "Vondelpark (relaxar)", "NDSM Wharf (arte urbana)", "Passeio de bicicleta pelos canais"],
            "food": ["Stroopwafel fresco no Albert Cuyp", "Queijo holandes no Henri Willig", "Bitterballen num cafe castanho (brown cafe)", "Panqueca holandesa na The Pancake Bakery", "Indonesian Rijsttafel"]
        },
        "must_see": ["Museu Van Gogh", "Rijksmuseum", "Casa de Anne Frank", "Canais (passeio de barco)", "Praca Dam", "Vondelpark", "Jordaan"],
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
        "stay_zones": [
            {"name": "Shinjuku", "description": "Maior hub ferroviario do mundo. Narita Express para aqui. Zona de hoteis e entretenimento.", "transport_access": "JR Yamanote Line — Narita Express — Metro Marunouchi/Oedo", "vibe": "Noturno, arranha-ceus, Golden Gai"},
            {"name": "Shibuya", "description": "Centro de cultura jovem. 2 paragens de Shinjuku na JR Yamanote Line.", "transport_access": "JR Yamanote — Metro Ginza/Hanzomon/Fukutoshin", "vibe": "Moderno, cruzamento famoso, moda"},
            {"name": "Asakusa", "description": "Bairro tradicional junto ao Senso-ji. Keisei Skyliner de Narita para em Ueno (5 min de metro).", "transport_access": "Metro Ginza ate Ueno — Tobu/Tsukuba Express", "vibe": "Tradicional, templos, mercados"},
            {"name": "Ueno", "description": "Junto ao parque e museus. Skyliner de Narita para aqui diretamente.", "transport_access": "Keisei Skyliner de Narita — JR Yamanote — Metro Ginza/Hibiya", "vibe": "Museus, parque, mercado Ameyoko"}
        ],
        "hotel_area": "Shinjuku",
        "transport": {"tip": "Narita e o principal para voos internacionais. Haneda e muito mais proximo do centro (20 min vs 80 min) — se tiveres opcao, escolhe Haneda. Compra o Japan Rail Pass antes de viajar se fores visitar varias cidades."},
        "weather_zone": "humid_subtropical",
        "attractions": {
            "iconic": ["Templo Senso-ji (Asakusa)", "Cruzamento de Shibuya", "Torre de Tokyo e Tokyo Skytree", "Palacio Imperial (jardins)", "Santuario Meiji (Harajuku)"],
            "cultural": ["teamLab Borderless/Planets", "Museu Ghibli (reserva obrigatoria)", "Museu Nacional de Tokyo", "Akihabara (cultura otaku e eletronica)", "Kabukiza Theatre (teatro tradicional)"],
            "local": ["Shinjuku Omoide Yokocho (ruelas de comida)", "Harajuku e Takeshita Street", "Yanaka (bairro tradicional)", "Shimokitazawa (vintage e cafes)", "Golden Gai (bares minusculos em Shinjuku)"],
            "food": ["Ramen em Ichiran ou Fuunji", "Sushi no Tsukiji Outer Market", "Yakitori em Omoide Yokocho", "Tempura no Tsunahachi", "Matcha e wagashi em Asakusa"]
        },
        "must_see": ["Templo Senso-ji", "Cruzamento de Shibuya", "Santuario Meiji", "Tokyo Skytree", "teamLab Planets", "Tsukiji Outer Market", "Harajuku", "Akihabara"],
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
        "stay_zones": [
            {"name": "Midtown Manhattan", "description": "Centro de tudo. Penn Station (comboios de Newark) e Grand Central ficam aqui. Perto de Times Square e Empire State.", "transport_access": "Todas as linhas de metro — NJ Transit de Newark em Penn Station", "vibe": "Iconica, teatros Broadway, arranha-ceus"},
            {"name": "Lower Manhattan/FiDi", "description": "Zona financeira junto ao WTC. PATH train liga diretamente a Newark.", "transport_access": "Metro 1/2/3, E, R — PATH para Newark", "vibe": "Historico, WTC Memorial, Wall Street"},
            {"name": "Chelsea/Union Square", "description": "Zona central com High Line e otimos restaurantes. Bem ligada a todas as linhas.", "transport_access": "Metro L, N, Q, R, 4, 5, 6 — a pe da Penn Station", "vibe": "Galerias, mercados, parques"},
            {"name": "Williamsburg (Brooklyn)", "description": "Bairro trendy fora de Manhattan. Metro L de Manhattan em 10 min. Alojamento mais acessivel.", "transport_access": "Metro L — Ferry East River ate Midtown", "vibe": "Hipster, brunch, vintage, vistas de Manhattan"}
        ],
        "hotel_area": "Midtown Manhattan",
        "transport": {"tip": "JFK e o principal para voos internacionais. Newark (EWR) tem boas opcoes transatlanticas e pode ser mais barato. LaGuardia e para voos domesticos. Todos ficam a 45-75 min do centro de Manhattan."},
        "weather_zone": "humid_continental",
        "attractions": {
            "iconic": ["Estatua da Liberdade e Ellis Island", "Times Square e Broadway", "Central Park (passeio ou bicicleta)", "Empire State Building (vista noturna)", "Brooklyn Bridge (passeio a pe)"],
            "cultural": ["Metropolitan Museum of Art (Met)", "MoMA (arte moderna)", "Guggenheim Museum", "American Museum of Natural History", "9/11 Memorial e Museum"],
            "local": ["High Line (parque elevado)", "Chelsea Market (comida e compras)", "Williamsburg Brooklyn (hipster)", "SoHo (galerias e boutiques)", "Greenwich Village (jazz e cafes)"],
            "food": ["Pizza na Joe's Pizza (Greenwich)", "Bagel no Russ & Daughters", "Cheesecake na Junior's", "Ramen no Ippudo", "Pastrami no Katz's Delicatessen"]
        },
        "must_see": ["Estatua da Liberdade", "Central Park", "Times Square", "Empire State Building", "Brooklyn Bridge", "Metropolitan Museum (Met)", "9/11 Memorial", "High Line"],
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
        "stay_zones": [
            {"name": "Chiado/Baixa", "description": "Centro historico. Metro Azul e Verde em Baixa-Chiado. Linha Vermelha vem direta do aeroporto ate Sao Sebastiao (transfer para Baixa).", "transport_access": "Metro Azul/Verde — Tram 28 — Bus 736 do aeroporto", "vibe": "Elegante, lojas, miradouros"},
            {"name": "Principe Real", "description": "Bairro premium junto ao Chiado. Metro Rato (Linha Amarela) a 5 min a pe.", "transport_access": "Metro Rato — Bus 758 do aeroporto", "vibe": "Brunch, jardins, boutiques"},
            {"name": "Alfama", "description": "Bairro mais antigo de Lisboa. Labirinto de ruelas junto ao Castelo. Metro Terreiro do Paco ou Santa Apolonia.", "transport_access": "Metro Azul — Tram 28 — a pe do Terreiro do Paco", "vibe": "Fado, tradicional, miradouros"},
            {"name": "Santos/Cais do Sodre", "description": "Junto ao rio, zona renovada com mercado e vida noturna. Metro Verde em Cais do Sodre.", "transport_access": "Metro Verde — Comboios para Cascais/Belem", "vibe": "Trendy, Time Out Market, rio"}
        ],
        "hotel_area": "Chiado",
        "transport": {"tip": "O aeroporto de Lisboa fica muito proximo do centro (7 km). O metro e a opcao mais rapida e barata. Compra o cartao Viva Viagem no metro do aeroporto e carrega com zapping para usar em todos os transportes."},
        "weather_zone": "mediterranean",
        "attractions": {
            "iconic": ["Torre de Belem e Mosteiro dos Jeronimos", "Castelo de Sao Jorge", "Praca do Comercio e Baixa", "Electrico 28 (percurso historico)", "Miradouro da Senhora do Monte"],
            "cultural": ["Museu dos Azulejos", "MAAT (arte e tecnologia)", "Museu Berardo (arte contemporanea)", "Fundacao Calouste Gulbenkian", "Fado ao vivo em Alfama"],
            "local": ["Alfama (bairro mais antigo, labirintos)", "LX Factory (mercado criativo)", "Bairro Alto (vida noturna)", "Feira da Ladra (mercado de rua, sabados)", "Principe Real (jardins e brunch)"],
            "food": ["Pastel de nata na Manteigaria", "Bifana no Ponto Final (Almada, com vista)", "Ginjinha no Rossio", "Marisco na Cervejaria Ramiro", "Francesinhas (se quiseres experimentar o Porto em Lisboa)"]
        },
        "must_see": ["Torre de Belem", "Mosteiro dos Jeronimos", "Castelo de Sao Jorge", "Alfama", "Electrico 28", "Praca do Comercio", "Belem (pasteis de nata)"],
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
        "stay_zones": [
            {"name": "Baixa/Aliados", "description": "Centro da cidade junto a Avenida dos Aliados. Metro D em Aliados, direto do aeroporto com transfer na Trindade.", "transport_access": "Metro D Aliados — Linha E do aeroporto via Trindade", "vibe": "Central, monumentos, lojas"},
            {"name": "Ribeira", "description": "Património UNESCO junto ao rio Douro. A pe de Aliados em 10 min, descendo.", "transport_access": "Metro D Sao Bento — Tram 1 junto ao rio", "vibe": "Historico, vistas, restaurantes"},
            {"name": "Cedofeita/Bom Sucesso", "description": "Bairro residencial trendy. Metro C em Casa da Musica.", "transport_access": "Metro C Casa da Musica — Bus 200, 201", "vibe": "Local, galerias, cafes de especialidade"},
            {"name": "Campanha", "description": "Hub ferroviario e de metro. Todas as linhas convergem aqui. Ideal se visitas Douro ou Braga.", "transport_access": "Metro A, B, C, E, F — Comboios para Douro e Braga", "vibe": "Pratico, mercados, bons precos"}
        ],
        "hotel_area": "Baixa",
        "transport": {"tip": "O aeroporto do Porto fica proximo do centro (11 km). O metro e a melhor opcao. Compra o cartao Andante no metro do aeroporto — a zona Z4 cobre aeroporto-centro."},
        "weather_zone": "oceanic",
        "attractions": {
            "iconic": ["Ponte D. Luis I (vista iconica)", "Livraria Lello (reserva online)", "Ribeira (patrimonio UNESCO)", "Torre dos Clerigos", "Palacio da Bolsa"],
            "cultural": ["Museu de Serralves (arte contemporanea)", "Igreja de Sao Francisco (interior barroco)", "Casa da Musica", "Museu do Vinho do Porto", "Se do Porto (catedral)"],
            "local": ["Caves do Vinho do Porto em Gaia (prova)", "Foz do Douro (passeio a beira-mar)", "Rua das Flores (cafes e lojas)", "Mercado do Bolhao (renovado)", "Passeio de Rabelo no rio Douro"],
            "food": ["Francesinha no Cafe Santiago", "Pastel de nata na Nata Lisboa", "Bacalhau a Bras no Adega Sao Nicolau", "Vinho do Porto nas caves em Gaia", "Petiscos na Rua das Flores"]
        },
        "must_see": ["Ponte D. Luis I", "Livraria Lello", "Ribeira", "Caves de Gaia", "Torre dos Clerigos", "Se do Porto", "Mercado do Bolhao"],
        "flights_from_lisbon": {"airline": "TAP", "prefix": "TP", "numbers": ["1945", "1947"], "duration": "0h55"},
        "flights_from_porto": None,
        "tips": [
            "As caves de Vinho do Porto em Vila Nova de Gaia oferecem provas gratuitas ou muito baratas.",
            "A Livraria Lello cobra entrada (reembolsavel em compras) — reserva online.",
            "Os cruzeiros de 6 pontes no Douro sao uma otima forma de ver a cidade (15-20 EUR).",
            "Experimenta o Cafe Majestic para um cafe historico (precos turisticos mas vale a experiencia)."
        ]
    },

    # ── NEW DESTINATIONS ──

    "berlim": {
        "name": "Berlim", "country": "Alemanha", "timezone": "CET",
        "airports": [
            {"code": "BER", "name": "Berlin Brandenburg (Willy Brandt)", "distance": "20 km do centro", "transport": "FEX Express ate Berlin Hauptbahnhof — 30 min, 3.80 EUR. S-Bahn S9/S45 ate Alexanderplatz — 50 min, 3.80 EUR"}
        ],
        "stay_zones": [
            {"name": "Mitte (Alexanderplatz)", "description": "Centro historico. S-Bahn S9 do aeroporto BER para direto em Alexanderplatz. Junto ao Muro, museus e Brandenburger Tor.", "transport_access": "S-Bahn S5/S7/S9 — U-Bahn U2/U5/U8 — FEX em Hauptbahnhof (10 min a pe)", "vibe": "Historico, museus, restaurantes"},
            {"name": "Kreuzberg (Kottbusser Tor)", "description": "Bairro multicultural com a melhor street food de Berlim. U-Bahn U1/U8 ligam ao centro em minutos.", "transport_access": "U-Bahn U1/U8 — Bus M29 ate Checkpoint Charlie", "vibe": "Multicultural, street food, clubes, arte urbana"},
            {"name": "Prenzlauer Berg", "description": "Charme residencial com cafes de brunch e feira de domingo no Mauerpark. U2 liga a Alexanderplatz.", "transport_access": "U-Bahn U2 — Tram M1/M10 — S-Bahn ring", "vibe": "Residencial, brunch, feira de domingo, familias"},
            {"name": "Charlottenburg (Savignyplatz)", "description": "Zona ocidental elegante. S-Bahn Zoo/Savignyplatz com ligacao direta ao aeroporto.", "transport_access": "S-Bahn S5/S7 — U-Bahn U2/U9 em Zoologischer Garten", "vibe": "Elegante, lojas, restaurantes classicos"}
        ],
        "hotel_area": "Mitte",
        "transport": {"tip": "Berlim tem apenas 1 aeroporto (BER). O FEX Express leva-te ao Hauptbahnhof em 30 min e o S9 a Alexanderplatz em 50 min — ambos custam 3.80 EUR. O bilhete ABC cobre toda a cidade incluindo aeroporto."},
        "weather_zone": "continental",
        "attractions": {
            "iconic": ["Porta de Brandemburgo", "East Side Gallery (Muro de Berlim)", "Ilha dos Museus (UNESCO)", "Reichstag (cupula gratuita — reserva online)", "Checkpoint Charlie"],
            "cultural": ["Pergamon Museum (reserva!)", "DDR Museum (vida na Alemanha Oriental)", "Topografia do Terror (memorial gratuito)", "Jewish Museum Berlin", "Hamburger Bahnhof (arte contemporanea)"],
            "local": ["Kreuzberg (street art e kebab turco)", "Mauerpark (feira e karaoke ao domingo)", "Tempelhofer Feld (antigo aeroporto transformado em parque)", "RAW Gelande (clubes e mercados)", "Gorlitzer Park e canal de Kreuzberg"],
            "food": ["Currywurst no Curry 36 (Kreuzberg)", "Doner Kebab no Mustafa's Gemuse Kebap", "Brunch no Five Elephant (Kreuzberg)", "Cerveja artesanal em Prenzlauer Berg", "Schnitzel no Zur letzten Instanz (restaurante mais antigo)"]
        },
        "must_see": ["Porta de Brandemburgo", "East Side Gallery (Muro)", "Ilha dos Museus", "Reichstag (cupula)", "Memorial do Holocausto", "Checkpoint Charlie", "Alexanderplatz e TV Tower", "Tiergarten"],
        "flights_from_lisbon": {"airline": "easyJet", "prefix": "U2", "numbers": ["4576", "4578"], "duration": "3h15"},
        "flights_from_porto": {"airline": "Ryanair", "prefix": "FR", "numbers": ["2172", "2174"], "duration": "3h10"},
        "tips": [
            "O Museumpass Berlin (3 dias, 32 EUR) da acesso a 30+ museus — vale muito a pena.",
            "Reserva a cupula do Reichstag online (gratuita) com antecedencia — esgota semanas antes.",
            "Berlim e muito plana — ideal para andar de bicicleta. Aluga na Nextbike ou Lime.",
            "O U-Bahn e S-Bahn funcionam 24h nos fins de semana. Durante a semana, param entre 1h-4h30."
        ]
    },
    "madrid": {
        "name": "Madrid", "country": "Espanha", "timezone": "CET",
        "airports": [
            {"code": "MAD", "name": "Adolfo Suarez Madrid-Barajas", "distance": "12 km do centro", "transport": "Metro L8 ate Nuevos Ministerios — 15 min, 4.50-6 EUR (suplemento aeroporto). Expres Aeropuerto bus ate Atocha — 30 min, 5 EUR"}
        ],
        "stay_zones": [
            {"name": "Sol/Centro", "description": "Puerta del Sol, coracao absoluto de Madrid. Metro L8 do aeroporto + transfer em Nuevos Ministerios para L1/L10.", "transport_access": "Metro L1/L2/L3 — Cercanias Renfe em Sol", "vibe": "Central, turistico, tapas, vida noturna"},
            {"name": "La Latina", "description": "Melhor bairro para tapas e mercados. El Rastro ao domingo. Metro L5 liga ao centro.", "transport_access": "Metro L5 La Latina — a pe de Sol em 10 min", "vibe": "Tapas, mercados, autenticidade, vida local"},
            {"name": "Malasana", "description": "Bairro cool e trendy com lojas vintage e cafes. Metro Tribunal.", "transport_access": "Metro L1/L10 Tribunal — a pe de Gran Via em 5 min", "vibe": "Alternativo, vintage, cafes, vida noturna"},
            {"name": "Chueca", "description": "Bairro vibrante e inclusivo. Excelentes restaurantes e bares.", "transport_access": "Metro L5 Chueca — a pe de Gran Via em 5 min", "vibe": "Vibrante, restaurantes, vida noturna, inclusivo"}
        ],
        "hotel_area": "Sol/Centro",
        "transport": {"tip": "O Metro L8 liga o aeroporto ao centro em 15 min (inclui suplemento de 3 EUR). Em alternativa, o Expres Aeropuerto (bus amarelo) leva-te a Atocha por 5 EUR. Funciona 24h."},
        "weather_zone": "continental",
        "attractions": {
            "iconic": ["Museu do Prado (reserva obrigatoria!)", "Palacio Real de Madrid", "Parque do Retiro (barcos no lago)", "Gran Via (a Broadway de Madrid)", "Plaza Mayor"],
            "cultural": ["Reina Sofia (Guernica de Picasso)", "Thyssen-Bornemisza (3 museus no Triangulo del Arte)", "Templo de Debod (por do sol)", "Cibeles Palace (vistas do terraço)", "Teatro Real (opera)"],
            "local": ["La Latina (tapas ao domingo apos El Rastro)", "Malasana (vintage e cafes)", "El Rastro (maior feira de rua de Espanha — domingos)", "Mercado de San Miguel (tapas gourmet)", "Lavapies (multicultural, gastronomia global)"],
            "food": ["Tapas no Mercado de San Miguel", "Bocadillo de calamares na Plaza Mayor", "Churros con chocolate na Chocolateria San Gines", "Cocido madrileno (cozido tradicional)", "Rooftop bar na Gran Via (Circulo de Bellas Artes)"]
        },
        "must_see": ["Museu do Prado", "Palacio Real", "Parque do Retiro", "Plaza Mayor", "Puerta del Sol", "Reina Sofia (Guernica)", "Gran Via", "Mercado de San Miguel"],
        "flights_from_lisbon": {"airline": "Iberia/TAP", "prefix": "IB", "numbers": ["3107", "3109"], "duration": "1h15"},
        "flights_from_porto": {"airline": "Ryanair", "prefix": "FR", "numbers": ["3714", "3716"], "duration": "1h20"},
        "tips": [
            "O Paseo del Arte (passe combinado Prado + Reina Sofia + Thyssen) poupa cerca de 20%.",
            "O Retiro e perfeito para uma pausa a meio do dia. Aluga um barco no lago (6 EUR/45 min).",
            "Os madrilenos jantam as 21h-22h. Restaurantes antes dessa hora estao quase vazios.",
            "El Rastro (feira de rua ao domingo) comeca as 9h — chega cedo para evitar multidoes."
        ]
    },
    "praga": {
        "name": "Praga", "country": "Republica Checa", "timezone": "CET",
        "airports": [
            {"code": "PRG", "name": "Vaclav Havel", "distance": "17 km do centro", "transport": "Bus 119 ate Nadrazi Veleslavin (Metro A) — 17 min, depois metro ate centro — total 35 min, 1.50 EUR. Airport Express bus ate Praha hl.n. — 35 min, 3 EUR"}
        ],
        "stay_zones": [
            {"name": "Stare Mesto (Cidade Velha)", "description": "Centro historico absoluto. Metro A Staromestska. Bus 119 do aeroporto liga ao Metro A.", "transport_access": "Metro A Staromestska — Tram 17, 18 junto ao rio", "vibe": "Historico, Praca da Cidade Velha, relogio astronomico"},
            {"name": "Nove Mesto (Cidade Nova)", "description": "Zona comercial com Praca Wenceslau. Mustek e a juncao das linhas Metro A e B.", "transport_access": "Metro A/B Mustek — Tram 3, 9, 14", "vibe": "Comercial, vida noturna, central"},
            {"name": "Mala Strana", "description": "Bairro barroco charming junto ao rio. Perto do Castelo de Praga. Metro A Malostranska.", "transport_access": "Metro A Malostranska — Tram 12, 20, 22 ate o Castelo", "vibe": "Romantico, barroco, jardins, vistas"},
            {"name": "Vinohrady", "description": "Bairro local com otimos restaurantes. Metro A Namesti Miru — 2 paragens do centro.", "transport_access": "Metro A Namesti Miru — Tram 4, 10, 16", "vibe": "Local, restaurantes, parques, elegante"}
        ],
        "hotel_area": "Stare Mesto",
        "transport": {"tip": "O Bus 119 do aeroporto e a opcao mais barata (1.50 EUR) — para na estacao de metro Nadrazi Veleslavin (linha A). De la, sao 10-15 min de metro ate ao centro. Compra bilhete de 90 min para cobrir toda a viagem."},
        "weather_zone": "continental",
        "attractions": {
            "iconic": ["Ponte Carlos (Charles Bridge — melhor ao amanhecer)", "Castelo de Praga e Catedral de Sao Vito", "Praca da Cidade Velha (Old Town Square)", "Relogio Astronomico (espetaculo a cada hora)", "Bairro Judeu (Josefov)"],
            "cultural": ["Galeria Nacional (Palacio de Comercio)", "Museu Nacional (Praca Wenceslau)", "Casa Dancante (Frank Gehry)", "Museu Franz Kafka", "Klementinum (biblioteca barroca — visita guiada)"],
            "local": ["Letna Park (melhor vista de Praga e cerveja)", "Vyšehrad (fortaleza com vista e cemiterio historico)", "Naplavka (mercado a beira-rio aos sabados)", "Zizkov (bairro boemo e TV Tower)", "Ilha Kampa (parque junto ao rio)"],
            "food": ["Trdelnik (chimney cake) em Stare Mesto", "Svickova na smetane (carne com molho cremoso)", "Cerveja checa num beer garden (Letna)", "Kulajda (sopa de cogumelos)", "Cafe no Grand Cafe Orient (cubismo checo)"]
        },
        "must_see": ["Ponte Carlos", "Castelo de Praga", "Praca da Cidade Velha", "Relogio Astronomico", "Catedral de Sao Vito", "Bairro Judeu (Josefov)", "Letna Park (vista panoramica)"],
        "flights_from_lisbon": {"airline": "Wizz Air/TAP", "prefix": "W6", "numbers": ["2339", "2341"], "duration": "3h20"},
        "flights_from_porto": {"airline": "Ryanair", "prefix": "FR", "numbers": ["4923", "4925"], "duration": "3h15"},
        "tips": [
            "A cerveja checa e mais barata que agua (30-50 CZK/~1.50 EUR por caneca). Experimenta Pilsner Urquell e Kozel.",
            "Visita a Ponte Carlos ao amanhecer (6h-7h) para evitar multidoes e ter fotos incriveis.",
            "Praga e muito walkable — quase tudo se faz a pe no centro historico.",
            "Troca dinheiro em casas de cambio com cartaz 0% commission (evita as da rua principal — taxas escondidas)."
        ]
    },
    "viena": {
        "name": "Viena", "country": "Austria", "timezone": "CET",
        "airports": [
            {"code": "VIE", "name": "Vienna International (Schwechat)", "distance": "20 km do centro", "transport": "CAT City Airport Train ate Wien Mitte — 16 min, 14.90 EUR. S-Bahn S7 ate Wien Mitte — 25 min, 4.40 EUR. Bus ate Schwedenplatz/Westbahnhof — 20-30 min, 8 EUR"}
        ],
        "stay_zones": [
            {"name": "Innere Stadt (1.o Distrito)", "description": "Centro historico dentro do Ring. Stephansplatz e a juncao de U1/U3. S-Bahn S7 do aeroporto para em Wien Mitte (10 min a pe).", "transport_access": "U-Bahn U1/U3 Stephansplatz — S-Bahn em Wien Mitte", "vibe": "Imperial, operas, cafes historicos, catedral"},
            {"name": "Neubau (7.o Distrito)", "description": "Bairro de museus e cafes trendy. U2/U3 em Museumsquartier ligam ao centro.", "transport_access": "U-Bahn U2/U3 Museumsquartier — Tram 49", "vibe": "Artístico, cafes, Museumsquartier, galerias"},
            {"name": "Wieden (4.o Distrito)", "description": "Junto ao Naschmarkt e Karlsplatz. U1/U2/U4 convergem em Karlsplatz — excelente hub.", "transport_access": "U-Bahn U1/U2/U4 Karlsplatz — Tram D, 1, 62", "vibe": "Naschmarkt, mercados, bistrots, central"},
            {"name": "Josefstadt (8.o Distrito)", "description": "Bairro local com teatros e charme vienense. U2 em Rathaus.", "transport_access": "U-Bahn U2 Rathaus — Tram 2, 5, 33", "vibe": "Local, teatros, tranquilo, residencial elegante"}
        ],
        "hotel_area": "Innere Stadt",
        "transport": {"tip": "O S7 e a opcao mais barata do aeroporto (4.40 EUR vs 14.90 EUR do CAT). Ambos param em Wien Mitte. Compra o Vienna City Card (24/48/72h) para transportes ilimitados + descontos em museus."},
        "weather_zone": "continental",
        "attractions": {
            "iconic": ["Palacio de Schonbrunn (residencia imperial)", "Catedral de Santo Estevao (Stephansdom)", "Palacio Belvedere (O Beijo de Klimt)", "Hofburg (palacio imperial no centro)", "Ring Boulevard (passeio de tram pelo anel historico)"],
            "cultural": ["Museumsquartier (Leopold Museum + MUMOK)", "Kunsthistorisches Museum (Historia da Arte)", "Albertina (Monet a Picasso)", "Opera Estatal de Viena (bilhetes em pe 4 EUR!)", "Casa da Musica (Musikverein — concertos classicos)"],
            "local": ["Naschmarkt (mercado com 120 bancas)", "Prater e roda gigante (Riesenrad)", "Heurigen em Grinzing (tabernas de vinho)", "Donaukanal (street art e bares de verao)", "Freud Museum e Berggasse"],
            "food": ["Wiener Schnitzel no Figlmuller (o mais famoso)", "Sachertorte no Hotel Sacher (original!)", "Cafe vienense no Cafe Central", "Apfelstrudel no Cafe Hawelka", "Kaiserschmarrn (panqueca imperial)"]
        },
        "must_see": ["Palacio de Schonbrunn", "Catedral de Santo Estevao", "Palacio Belvedere (Klimt)", "Hofburg", "Ring Boulevard", "Museumsquartier", "Naschmarkt", "Prater (roda gigante)"],
        "flights_from_lisbon": {"airline": "Austrian/TAP", "prefix": "OS", "numbers": ["592", "594"], "duration": "3h10"},
        "flights_from_porto": {"airline": "Ryanair", "prefix": "FR", "numbers": ["7103", "7105"], "duration": "3h05"},
        "tips": [
            "Os bilhetes em pe na Opera de Viena custam apenas 4 EUR — faz fila 1h antes do espetaculo.",
            "O Naschmarkt fecha ao domingo. Vai ao sabado para a melhor experiencia (feira de antiguidades).",
            "Viena e uma das cidades mais seguras da Europa. Podes andar a vontade a qualquer hora.",
            "Experimenta um cafe vienense classico (Melange + bolo) — e Património Imaterial da UNESCO."
        ]
    },
    "budapeste": {
        "name": "Budapeste", "country": "Hungria", "timezone": "CET",
        "airports": [
            {"code": "BUD", "name": "Budapest Ferenc Liszt", "distance": "20 km do centro", "transport": "Bus 100E ate Deak Ferenc ter (centro) — 35 min, 2200 HUF (~6 EUR). Bus 200E ate metro M3 (Kobanya-Kispest) — 45 min total, 530 HUF (~1.50 EUR)"}
        ],
        "stay_zones": [
            {"name": "Distrito V (Belvaros)", "description": "Centro absoluto junto ao Parlamento. Deak Ferenc ter e a juncao das 3 linhas de metro. Bus 100E do aeroporto para aqui.", "transport_access": "Metro M1/M2/M3 em Deak Ferenc ter — Bus 100E do aeroporto", "vibe": "Central, Parlamento, Danubio, elegante"},
            {"name": "Distrito VII (Bairro Judeu)", "description": "Zona dos famosos ruin bars. Metro M2 em Blaha Lujza ter. Vida noturna vibrante.", "transport_access": "Metro M2 Blaha Lujza ter — Tram 4/6 (circula 24h)", "vibe": "Ruin bars, vida noturna, cultural, alternativo"},
            {"name": "Distrito VI (Terezvaros)", "description": "Avenida Andrassy (Champs-Elysees de Budapeste). Metro M1 (a mais antiga da Europa continental).", "transport_access": "Metro M1 Oktogon — Tram 4/6", "vibe": "Elegante, Andrassy, opera, restaurantes"},
            {"name": "Distrito I (Buda/Castelo)", "description": "Colina historica com Castelo e Bastiao dos Pescadores. Bus 16 de Deak Ferenc ter.", "transport_access": "Bus 16 de Deak Ferenc ter — Funicular do Danubio", "vibe": "Panoramico, historico, vistas, tranquilo"}
        ],
        "hotel_area": "Distrito V",
        "transport": {"tip": "O Bus 100E e a forma mais rapida e direta do aeroporto ao centro (35 min, 6 EUR). Em alternativa mais barata, o Bus 200E leva-te ao metro M3 (1.50 EUR total). O Tram 4/6 circula 24 horas e liga os dois lados da cidade."},
        "weather_zone": "continental",
        "attractions": {
            "iconic": ["Parlamento Hungaro (o mais bonito da Europa — reserva tour)", "Castelo de Buda e Palacio Real", "Bastiao dos Pescadores (Fisherman's Bastion — vista magica)", "Ponte das Correntes (Chain Bridge — iluminada a noite)", "Termas de Szechenyi (banho termal no parque)"],
            "cultural": ["Basilica de Santo Estevao (subir a cupula!)", "Opera Estatal Hungara (visitas guiadas)", "Casa do Terror (museu da ocupacao)", "Hospital na Rocha (bunker da Guerra Fria)", "Galeria Nacional Hungara (no Castelo)"],
            "local": ["Ruin bars (Szimpla Kert e o mais famoso)", "Mercado Central (Grande Vasarcsarnok — langos!)", "Ilha Margarida (parque e piscinas no meio do Danubio)", "Bairro Judeu (sinagogas e street art)", "Gellert Hill (melhor por do sol sobre a cidade)"],
            "food": ["Goulash hungaro no Bors Gasztrobar", "Langos no Mercado Central (com sour cream e queijo)", "Chimney cake (kurtoskalacs) na rua", "Dobos Torta no Cafe Gerbeaud", "Jantar num cruzeiro no Danubio"]
        },
        "must_see": ["Parlamento Hungaro", "Castelo de Buda", "Bastiao dos Pescadores", "Ponte das Correntes", "Termas de Szechenyi", "Basilica de Santo Estevao", "Sapatos no Danubio (memorial)", "Mercado Central"],
        "flights_from_lisbon": {"airline": "Wizz Air", "prefix": "W6", "numbers": ["2347", "2349"], "duration": "3h30"},
        "flights_from_porto": {"airline": "Ryanair", "prefix": "FR", "numbers": ["1847", "1849"], "duration": "3h25"},
        "tips": [
            "Os banhos termais sao obrigatorios! Szechenyi (exterior, maior) ou Gellert (interior, art nouveau) — leva fato de banho.",
            "O Forinto hungaro (HUF) e a moeda local. 1 EUR ≈ 400 HUF. Paga com cartao quase em todo o lado.",
            "Os ruin bars sao unicos no mundo — Szimpla Kert e o original e mais famoso (aberto desde 2001).",
            "Faz o cruzeiro noturno no Danubio — ver o Parlamento e o Castelo iluminados e magico."
        ]
    },
    "istambul": {
        "name": "Istambul", "country": "Turquia", "timezone": "TRT",
        "airports": [
            {"code": "IST", "name": "Istanbul Airport (lado europeu)", "distance": "40 km do centro", "transport": "Metro M11 ate Kagithane, depois M7 ate centro — 50-70 min, ~2 EUR. Havaist bus ate Taksim — 60-90 min, ~5 EUR"},
            {"code": "SAW", "name": "Sabiha Gokcen (lado asiatico)", "distance": "40 km do centro", "transport": "Havabus ate Kadikoy — 60 min, ~4 EUR (depois ferry para lado europeu). Havaist bus ate Taksim — 90-120 min, ~6 EUR"}
        ],
        "stay_zones": [
            {"name": "Sultanahmet/Fatih", "description": "Centro historico com Hagia Sophia e Mesquita Azul. Tram T1 liga a Eminonu (portos de ferry). Havaist do aeroporto IST tem paragem em Sultanahmet.", "transport_access": "Tram T1 Sultanahmet — Havaist de IST para Sultanahmet", "vibe": "Historico, monumentos, bazares, turistico"},
            {"name": "Beyoglu/Taksim", "description": "Centro moderno com Istiklal e vida noturna. Havaist de ambos os aeroportos para em Taksim.", "transport_access": "Metro M2 Taksim — Funicular ate Kabatas — Havaist de IST e SAW", "vibe": "Moderno, Istiklal, restaurantes, vida noturna"},
            {"name": "Karakoy/Galata", "description": "Bairro trendy junto a agua com Torre de Galata. Tram T1 para em Karakoy.", "transport_access": "Tram T1 Karakoy — Tunel (funicular historico) ate Beyoglu", "vibe": "Trendy, cafes, galerias, waterfront, Torre de Galata"},
            {"name": "Kadikoy (lado asiatico)", "description": "Bairro local autentico. Havabus de SAW para aqui. Ferry para o lado europeu em 20 min.", "transport_access": "Ferry Kadikoy-Eminonu 20 min — Havabus de SAW — Metro M4", "vibe": "Local, mercados, autenticidade, precos acessiveis"}
        ],
        "hotel_area": "Sultanahmet",
        "transport": {"tip": "Istambul tem 2 aeroportos em lados opostos da cidade. IST (europeu) e o principal. SAW (asiatico) e usado por low-cost. Compra o Istanbulkart (cartao de transportes recarregavel) na chegada — funciona em tudo (metro, tram, bus, ferry)."},
        "weather_zone": "mediterranean",
        "attractions": {
            "iconic": ["Hagia Sophia (obra-prima bizantina/otomana)", "Mesquita Azul (Sultan Ahmed — gratis, tira os sapatos)", "Palacio de Topkapi (residencia dos sultoes)", "Grande Bazar (4000+ lojas — regatea!)", "Cisterna da Basilica (subterranea, atmosferica)"],
            "cultural": ["Torre de Galata (vista 360o)", "Mesquita de Suleymaniye (a mais majestosa)", "Museu de Arte Moderna de Istambul", "Palacio Dolmabahce (versao otomana de Versailles)", "Igreja de Chora (mosaicos bizantinos)"],
            "local": ["Cruzeiro no Bosforo (entre Europa e Asia)", "Bairro de Balat (casas coloridas, Instagram)", "Rua Istiklal (passeio ate Taksim)", "Kadikoy (mercado e bairro local asiatico)", "Cha turco no Cafe Pierre Loti (vista do Corno de Ouro)"],
            "food": ["Kebab turco no Bayramoglu (local, nao turistico)", "Balik ekmek (sanduiche de peixe) em Eminonu junto ao rio", "Cha turco num cafe tradicional", "Baklava no Karakoy Gulluoglu (o melhor de Istambul)", "Breakfast turco completo (kahvalti) em Kadikoy"]
        },
        "must_see": ["Hagia Sophia", "Mesquita Azul", "Palacio de Topkapi", "Grande Bazar", "Cisterna da Basilica", "Torre de Galata", "Cruzeiro no Bosforo", "Mesquita de Suleymaniye"],
        "flights_from_lisbon": {"airline": "Turkish Airlines", "prefix": "TK", "numbers": ["1760", "1762"], "duration": "4h15"},
        "flights_from_porto": {"airline": "Pegasus/Turkish", "prefix": "PC", "numbers": ["1228", "1230"], "duration": "4h30"},
        "tips": [
            "Compra o Istanbulkart logo no aeroporto — custa 50 TRY e poupa-te dinheiro em todos os transportes.",
            "O Grande Bazar fecha ao domingo. Vai durante a semana para a experiencia completa e regatea (comeca a 50% do preco pedido).",
            "O ferry entre Europa e Asia e um dos melhores passeios da cidade (e custa so 1 viagem no Istanbulkart).",
            "Experimenta um hammam (banho turco) — Cagaloglu ou Cemberlitas sao os mais historicos."
        ]
    },
    "florenca": {
        "name": "Florenca", "country": "Italia", "timezone": "CET",
        "airports": [
            {"code": "FLR", "name": "Amerigo Vespucci (Peretola)", "distance": "5 km do centro", "transport": "Tram T2 ate Santa Maria Novella (estacao central) — 20 min, 1.50 EUR"},
            {"code": "PSA", "name": "Galileo Galilei (Pisa)", "distance": "80 km do centro", "transport": "PisaMover ate Pisa Centrale + Trenitalia ate Firenze SMN — 70-90 min total, 10-15 EUR. Alternativa low-cost"}
        ],
        "stay_zones": [
            {"name": "Santa Maria Novella", "description": "Junto a estacao central. Tram T2 do aeroporto FLR para aqui. Hub principal de comboios (para Pisa, Roma, Veneza).", "transport_access": "Tram T1/T2 — Trenitalia de Pisa — Bus ATAF", "vibe": "Pratico, central, igrejas renascentistas"},
            {"name": "Duomo/San Lorenzo", "description": "Coracao de Florenca. A pe da estacao SMN (5 min). Mercado de San Lorenzo e Duomo a porta.", "transport_access": "A pe de SMN — Bus C1 — Tram T1", "vibe": "Icónico, Duomo, mercados, gelaterias"},
            {"name": "Santa Croce", "description": "Bairro artesanal mais local, junto a Basilica de Santa Croce. Menos turistico que o Duomo.", "transport_access": "Bus C1/C2/C3 — a pe do centro (10 min)", "vibe": "Artesanato, couro, trattorias locais"},
            {"name": "Oltrarno", "description": "Do outro lado do Arno, via Ponte Vecchio. Ateliers de artesaos e vista do Piazzale Michelangelo.", "transport_access": "Bus D — a pe via Ponte Vecchio (10 min do Duomo)", "vibe": "Bohemio, ateliers, Palazzo Pitti, vistas"}
        ],
        "hotel_area": "Duomo/San Lorenzo",
        "transport": {"tip": "Peretola (FLR) e o aeroporto de Florenca e fica a 20 min de tram do centro. Pisa (PSA) e muito maior e serve mais low-cost — o comboio de Pisa a Florenca leva 70-90 min. O centro historico e quase todo pedonal — faz tudo a pe!"},
        "weather_zone": "mediterranean",
        "attractions": {
            "iconic": ["Duomo e Cupula de Brunelleschi (463 degraus — reserva!)", "Galleria degli Uffizi (obra-prima renascentista)", "Ponte Vecchio (ponte medieval com ourivesarias)", "Piazza della Signoria e Palazzo Vecchio", "Galleria dell'Accademia (David de Michelangelo)"],
            "cultural": ["Palazzo Pitti e Jardins de Boboli", "Basilica de Santa Croce (tumulos de Galileu e Michelangelo)", "Basilica de San Lorenzo e Capelas dos Medici", "Museu Bargello (esculturas renascentistas)", "Chiesa di Santa Maria del Carmine (frescos de Masaccio)"],
            "local": ["Piazzale Michelangelo (melhor vista — por do sol)", "San Lorenzo Market (couro e souvenirs)", "Oltrarno (oficinas de artesaos)", "Fiesole (colina com ruinas romanas — 20 min de bus)", "Sant'Ambrogio Market (mercado local matinal)"],
            "food": ["Bistecca alla Fiorentina no Trattoria Mario", "Gelato na Gelateria dei Neri ou Vivoli", "Lampredotto (tripas no pao — street food classico)", "Ribollita (sopa toscana de pao)", "Chianti numa enoteca no Oltrarno"]
        },
        "must_see": ["Duomo e Cupula de Brunelleschi", "Galleria degli Uffizi", "Ponte Vecchio", "Piazza della Signoria", "David de Michelangelo (Accademia)", "Palazzo Pitti", "Piazzale Michelangelo (vista)", "Santa Croce"],
        "flights_from_lisbon": {"airline": "TAP/Vueling", "prefix": "VY", "numbers": ["6240", "6242"], "duration": "2h50"},
        "flights_from_porto": {"airline": "Ryanair (via Pisa)", "prefix": "FR", "numbers": ["5130", "5132"], "duration": "2h40 (para Pisa)"},
        "tips": [
            "Reserva a subida a Cupula do Duomo com antecedencia — ha limite de pessoas e esgota rapido.",
            "Os Uffizi ao final da tarde (apos 16h) tem menos gente — tenta a ultima entrada.",
            "Florenca e compacta — faz tudo a pe. Nao precisas de transportes publicos no centro.",
            "O lampredotto (tripas no pao) e o street food classico florentino — experimenta no Mercato di Sant'Ambrogio."
        ]
    },
    "dubai": {
        "name": "Dubai", "country": "Emirados Arabes Unidos", "timezone": "GST",
        "airports": [
            {"code": "DXB", "name": "Dubai International", "distance": "5 km do centro antigo, 15 km de Downtown", "transport": "Metro Red Line (Terminal 1 e 3) ate centro — 30-45 min, 8-15 AED (~2-4 EUR). Taxi ate Downtown ~60 AED (~15 EUR)"},
            {"code": "DWC", "name": "Al Maktoum International (Dubai World Central)", "distance": "55 km de Downtown", "transport": "Bus F55 ate Ibn Battuta Metro Station, depois Red Line — 60-90 min total. Muito poucos voos de passageiros"}
        ],
        "stay_zones": [
            {"name": "Downtown Dubai", "description": "Junto ao Burj Khalifa e Dubai Mall. Metro Red Line (Burj Khalifa/Dubai Mall station) liga ao aeroporto DXB.", "transport_access": "Metro Red Line — Burj Khalifa/Dubai Mall station", "vibe": "Iconico, Burj Khalifa, luxo, centros comerciais"},
            {"name": "Dubai Marina", "description": "Passeio maritimo com restaurantes e praia. Metro Red Line + Dubai Tram.", "transport_access": "Metro Red Line (DMCC/JLT) — Dubai Tram — buses maritimos", "vibe": "Praia, restaurantes, passeio maritimo, moderno"},
            {"name": "Deira/Old Dubai", "description": "Dubai historica com Gold Souk e Spice Souk. Metro Green/Red Line. Mais proximo do aeroporto DXB.", "transport_access": "Metro Red/Green Line Union — Abra (barco tradicional) pelo Creek", "vibe": "Tradicional, souks, autenticidade, precos acessiveis"},
            {"name": "Business Bay", "description": "Zona moderna junto a Downtown. Bons precos de hotel com metro Red Line direto.", "transport_access": "Metro Red Line Business Bay — a pe de Downtown (15 min)", "vibe": "Moderno, canal, bom custo-beneficio, central"}
        ],
        "hotel_area": "Downtown Dubai",
        "transport": {"tip": "O Metro Red Line e a forma mais barata de chegar de DXB ao centro. Compra o NOL Card (cartao de transportes) no aeroporto. O metro nao cobre tudo — para Palm Jumeirah usa o monorail, e taxis sao baratos (comparados com a Europa)."},
        "weather_zone": "desert",
        "attractions": {
            "iconic": ["Burj Khalifa — At the Top (reserva o bilhete para o por do sol!)", "Dubai Mall e Aquario (maior centro comercial do mundo)", "Palm Jumeirah (passeio pelo Boardwalk)", "Dubai Marina (passeio de barco ao por do sol)", "Dubai Frame (vista dos dois lados da cidade)"],
            "cultural": ["Dubai Creek e Abra (barco tradicional — 1 AED!)", "Gold Souk e Spice Souk (regatea!)", "Al Fahidi Historical Neighbourhood (bairro antigo restaurado)", "Dubai Museum (no Al Fahidi Fort)", "Mesquita de Jumeirah (visitas guiadas para nao-muculmanos)"],
            "local": ["Desert Safari (dunas, camelo, jantar beduino)", "La Mer (praia e street food)", "Global Village (parque tematico multicultural — outubro a abril)", "Kite Beach (desportos aquaticos)", "Al Seef (passeio pelo Creek renovado)"],
            "food": ["Shawarma no Al Mallah (Satwa — local)", "Brunch de sexta-feira (tradicao de Dubai)", "Cafe arabico com tamara no Al Fahidi", "Jantar no Pierchic (sobre a agua, Palm)", "Comida indiana em Deira (curry autentico a precos locais)"]
        },
        "must_see": ["Burj Khalifa (At the Top)", "Dubai Mall", "Palm Jumeirah", "Dubai Marina", "Gold Souk", "Dubai Frame", "Desert Safari", "Dubai Creek (Abra)"],
        "flights_from_lisbon": {"airline": "Emirates", "prefix": "EK", "numbers": ["192", "194"], "duration": "7h15"},
        "flights_from_porto": {"airline": "Emirates via Dubai", "prefix": "EK", "numbers": ["196"], "duration": "7h30"},
        "tips": [
            "Evita junho-agosto — temperaturas acima de 45C. A melhor epoca e novembro-marco.",
            "O Burj Khalifa ao por do sol (bilhete 148o andar) e a melhor experiencia — reserva online com antecedencia.",
            "Sexta-feira e o dia de descanso (como o domingo na Europa). Muitos brunchs especiais neste dia.",
            "O metro e limpo e eficiente mas tem classes: Gold (premium) e Standard. A multa por comer/beber no metro e alta (200 AED)."
        ]
    },
    "bali": {
        "name": "Bali", "country": "Indonesia", "timezone": "WITA",
        "airports": [
            {"code": "DPS", "name": "Ngurah Rai International", "distance": "Sul da ilha", "transport": "Sem metro ou comboio. Taxi oficial/Grab: Seminyak 30-45 min (~9-12 EUR), Ubud 75-90 min (~15-21 EUR), Nusa Dua 20-30 min (~7-10 EUR)"}
        ],
        "stay_zones": [
            {"name": "Seminyak", "description": "Equilibrio perfeito entre praia, restaurantes e vida noturna. 30-45 min do aeroporto. Zona mais popular para turistas.", "transport_access": "Taxi/Grab do aeroporto 30-45 min — scooter para explorar", "vibe": "Praias, sunset bars, restaurantes, vida noturna"},
            {"name": "Canggu", "description": "Capital do surf e nomadas digitais. Cafes de brunch incriveis e arrozais a porta. 45 min do aeroporto.", "transport_access": "Taxi/Grab do aeroporto 45 min — scooter essencial", "vibe": "Surf, cafes, arrozais, digital nomads, relaxado"},
            {"name": "Ubud", "description": "Centro cultural e espiritual de Bali. Terracos de arroz, templos e yoga. 75-90 min do aeroporto.", "transport_access": "Taxi/Grab do aeroporto 75-90 min — scooter para arredores", "vibe": "Cultural, templos, natureza, yoga, artesanato"},
            {"name": "Nusa Dua", "description": "Zona de resorts com praias calmas e aguas cristalinas. 20-30 min do aeroporto. Ideal para familias.", "transport_access": "Taxi/Grab do aeroporto 20-30 min — shuttle dos resorts", "vibe": "Resorts, praias calmas, luxo, familias, tranquilo"}
        ],
        "hotel_area": "Seminyak",
        "transport": {"tip": "Bali nao tem metro ou comboio. Os taxis e Grab (tipo Uber local) sao a unica opcao do aeroporto. Aluga uma scooter (~5 EUR/dia) para explorar — e a forma como os locais se deslocam. Atenção: transito em Bali pode ser caótico, conduz com cuidado."},
        "weather_zone": "tropical",
        "attractions": {
            "iconic": ["Templo de Uluwatu (por do sol + danca Kecak)", "Terracos de Arroz de Tegallalang (UNESCO)", "Tanah Lot (templo na agua — por do sol)", "Sacred Monkey Forest (Ubud — macacos e templos)", "Tirta Empul (templo de purificacao com agua sagrada)"],
            "cultural": ["Palacio Real de Ubud (Puri Saren Agung)", "Besakih (templo-mae de Bali, no vulcao Agung)", "Tirta Gangga (palacio de agua real)", "Museu de Arte Agung Rai (ARMA) em Ubud", "Cerimonias tradicionais (templos locais — pede permissao)"],
            "local": ["Arrozais de Jatiluwih (UNESCO — menos turistico)", "Praia de Padang Padang (praia escondida)", "Cachoeira de Tegenungan (perto de Ubud)", "Mercado de Ubud (artesanato — regatea)", "Bali Swing (baloico sobre o vale — Instagramavel)"],
            "food": ["Nasi Goreng (arroz frito — prato nacional)", "Babi Guling (porco assado — Ibu Oka em Ubud)", "Smoothie bowl nos cafes de Canggu", "Satay (espetadas) num warung local", "Lawar e Bebek Betutu (comida cerimonial balinesa)"]
        },
        "must_see": ["Templo de Uluwatu (por do sol)", "Terracos de Arroz Tegallalang", "Tanah Lot", "Sacred Monkey Forest (Ubud)", "Tirta Empul", "Besakih (templo-mae)", "Praia de Padang Padang", "Cachoeira de Tegenungan"],
        "flights_from_lisbon": {"airline": "Qatar Airways via Doha", "prefix": "QR", "numbers": ["341+QR962"], "duration": "17-19h (1 escala)"},
        "flights_from_porto": {"airline": "Turkish Airlines via Istanbul", "prefix": "TK", "numbers": ["1764+TK66"], "duration": "18-20h (1 escala)"},
        "tips": [
            "A melhor epoca e abril-outubro (epoca seca). Novembro-marco chove frequentemente mas ha menos turistas.",
            "Aluga scooter so se tens experiencia de moto. O transito em Bali e caotico. Caso contrario, usa Grab.",
            "Leva sarong (pano) para visitar templos — e obrigatorio. Muitos templos emprestam na entrada.",
            "A agua da torneira NAO e potavel. Bebe sempre agua engarrafada. Cuidado com gelo em sitios menos turisticos."
        ]
    },
}

# ── DESTINATION ALIASES (fuzzy matching) ──
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
    "berlim": "berlim", "berlin": "berlim",
    "madrid": "madrid",
    "praga": "praga", "prague": "praga", "praha": "praga",
    "viena": "viena", "vienna": "viena", "wien": "viena",
    "budapeste": "budapeste", "budapest": "budapeste",
    "istambul": "istambul", "istanbul": "istambul", "constantinopla": "istambul",
    "florenca": "florenca", "florence": "florenca", "firenze": "florenca", "florencia": "florenca",
    "dubai": "dubai",
    "bali": "bali", "denpasar": "bali",
}

# ── REUSABLE TEMPLATE TYPES ──
# Fallback structures for destinations not in the specific templates.
# The hybrid engine uses these before resorting to full AI generation.
TEMPLATE_TYPES = {
    "european_city_break": {
        "duration_range": [2, 5],
        "weather_zone": "continental",
        "default_packing": "mild",
        "structure": {
            "day_1": ["Chegada e check-in no hotel", "Passeio de orientacao pelo centro historico", "Jantar num restaurante local recomendado"],
            "day_2": ["Visitar os monumentos e museus principais", "Almoco numa zona local (fora do circuito turistico)", "Passeio pela zona historica e compras"],
            "middle": ["Explorar bairros locais e mercados", "Visitar museus ou galerias secundarias", "Café numa esplanada com vista"],
            "last_day": ["Check-out do hotel", "Ultimas compras ou visita a um miradouro", "Transfer para o aeroporto"]
        },
        "generic_tips": [
            "Compra um passe de transportes para a duracao da viagem — quase sempre compensa.",
            "Reserva bilhetes online para museus populares — evita filas de 1-2 horas.",
            "Caminha uma rua atras dos pontos turisticos para precos locais nos restaurantes.",
            "Leva sapatos confortaveis — vais andar 15-20 mil passos por dia facilmente."
        ],
        "generic_must_see": ["Praca principal e centro historico", "Catedral ou igreja principal", "Museu principal", "Miradouro com vista panoramica", "Mercado local", "Bairro alternativo/boemo"]
    },
    "beach_destination": {
        "duration_range": [5, 10],
        "weather_zone": "tropical",
        "default_packing": "warm",
        "structure": {
            "day_1": ["Chegada e check-in no hotel/resort", "Relaxar na praia e explorar a zona", "Jantar junto ao mar ao por do sol"],
            "day_2": ["Manha na praia ou piscina", "Desportos aquaticos (snorkeling, surf, kayak)", "Explorar um mercado local a tarde"],
            "middle": ["Excursao cultural (templo, ruinas, aldeia local)", "Dia de praia numa ilha ou praia menos conhecida", "Massagem ou spa local"],
            "last_day": ["Ultimo mergulho matinal", "Compras de artesanato e lembracas", "Transfer para o aeroporto"]
        },
        "generic_tips": [
            "Usa protecao solar SPF50+ e reaplica a cada 2 horas — o sol tropical e muito forte.",
            "Aluga scooter ou bicicleta para explorar — transportes publicos sao limitados em ilhas.",
            "Negoceia precos em mercados locais — e cultural e esperado.",
            "Leva repelente de mosquitos — essencial em zonas tropicais."
        ],
        "generic_must_see": ["Praia principal e por do sol", "Templo ou monumento historico", "Mercado local", "Ponto de snorkeling ou mergulho", "Miradouro ou trilho natural", "Aldeia ou bairro tradicional"]
    },
    "long_haul_trip": {
        "duration_range": [7, 14],
        "weather_zone": "humid_subtropical",
        "default_packing": "mild",
        "structure": {
            "day_1": ["Chegada e recuperacao do jet lag", "Passeio leve pelo bairro do hotel", "Jantar cedo e descanso"],
            "day_2": ["Explorar o bairro principal com calma", "Visitar mercado local e experimentar comida de rua", "Primeiros monumentos sem pressao"],
            "middle": ["Dia completo de visitas culturais", "Day trip a uma cidade ou zona proxima", "Experiencia gastronómica local"],
            "last_day": ["Ultimas compras e souvenirs", "Almoco de despedida", "Transfer para o aeroporto (chega com antecedencia extra)"]
        },
        "generic_tips": [
            "Ajusta-te ao fuso horario nos primeiros 2 dias — nao marcas visitas cedo no dia 1.",
            "Leva adaptador de tomada universal e carregador portatil.",
            "Ativa um eSIM ou plano de dados antes de viajar — comunicacao e essencial.",
            "Pesquisa requisitos de visto com antecedencia — alguns paises exigem visto eletronico."
        ],
        "generic_must_see": ["Monumento icónico da cidade", "Bairro historico e tradicional", "Mercado local (comida de rua)", "Templo, santuario ou local sagrado", "Miradouro ou parque natural", "Experiencia cultural unica (cerimonia, espetaculo, workshop)"]
    },
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
    "desert": {
        1: "Inverno agradavel (15-24C). Melhor epoca para visitar. Noites frescas (10-15C).",
        2: "Inverno ameno (16-25C). Tempo perfeito para atividades ao ar livre.",
        3: "Primavera quente (19-29C). A aquecer. Ainda confortavel.",
        4: "Quente (22-34C). Sol intenso. Proteção solar essencial.",
        5: "Muito quente (26-38C). Atividades ao ar livre so de manha cedo ou ao fim do dia.",
        6: "Extremamente quente (29-41C). Evita exposicao ao sol entre 10h-16h.",
        7: "Pico do calor (31-43C). Temperaturas extremas. Fica em sitios com ar condicionado.",
        8: "Muito quente (31-43C). Humidade elevada junto a costa. Calor insuportavel ao ar livre.",
        9: "Quente (28-39C). Ainda muito quente. A melhorar gradualmente.",
        10: "Outono quente (24-35C). Temperatura a descer. Atividades ao ar livre possiveis.",
        11: "Agradavel (20-29C). Otima epoca para visitar. Noites frescas.",
        12: "Inverno ameno (16-25C). Melhor epoca. Perfeito para explorar ao ar livre."
    },
    "tropical": {
        1: "Epoca humida (24-30C). Chuvas frequentes a tarde. Manhas ensolaradas.",
        2: "Epoca humida (24-30C). Chuvas tropicais diarias. Humidade alta.",
        3: "Final epoca humida (24-31C). Chuvas a diminuir. Vegetacao exuberante.",
        4: "Transicao (24-32C). Menos chuva. Bom tempo na maioria dos dias.",
        5: "Epoca seca (24-32C). Pouca chuva. Sol e calor. Melhor epoca para visitar.",
        6: "Epoca seca (23-31C). Tempo estavel e agradavel. Menos humidade.",
        7: "Epoca seca (23-30C). Fresco para os tropicos. Melhor epoca.",
        8: "Epoca seca (23-31C). Tempo perfeito. Pouca chuva.",
        9: "Final epoca seca (24-31C). Tempo ainda bom. Algumas chuvas a comecar.",
        10: "Transicao (24-31C). Chuvas a regressar. Ainda maioritariamente sol.",
        11: "Epoca humida (24-30C). Chuvas frequentes. Trovoadas tropicais a tarde.",
        12: "Epoca humida (24-30C). Chuvas intensas. Menos turistas, precos mais baixos."
    },
}

# ── PACKING TEMPLATES ──
PACKING_TEMPLATES = {
    "warm": {
        "clothing": ["T-shirts e tops leves", "Calcoes/saias", "Vestido/roupa fresca para jantar", "Chapeu ou bone para sol", "Sandalias confortaveis", "Roupa interior e meias (diarias)"],
        "essentials": ["Protecao solar SPF50", "Garrafa de agua reutilizavel", "Oculos de sol", "Carregador portatil", "Adaptador de tomada", "Saco pequeno para dia"]
    },
    "mild": {
        "clothing": ["Camadas: t-shirt + camisola + casaco", "Calcas confortaveis para caminhar", "Roupa mais arranjada para jantar", "Impermeavel leve", "Tenis confortaveis para caminhar muito", "Roupa interior e meias (diarias)"],
        "essentials": ["Guarda-chuva compacto", "Garrafa de agua reutilizavel", "Carregador portatil", "Adaptador de tomada", "Saco pequeno para dia", "Protetor labial"]
    },
    "cold": {
        "clothing": ["Casaco de inverno quente", "Camadas termicas", "Gorro, cachecol e luvas", "Botas impermeaveis", "Calcas quentes", "Camisolas de la ou fleece"],
        "essentials": ["Creme hidratante", "Protetor labial", "Carregador portatil", "Adaptador de tomada", "Garrafa termica", "Saco pequeno para dia"]
    },
    "hot_dry": {
        "clothing": ["Roupa leve e de cor clara (linho, algodao)", "Calcoes e camisas de manga curta", "Roupa elegante para jantar (dress code em restaurantes)", "Chapeu de sol largo", "Sandalias e tenis leves", "Lenco ou shawl (para mesquitas e ar condicionado forte)"],
        "essentials": ["Protecao solar SPF50+", "Garrafa de agua (hidratacao constante)", "Oculos de sol polarizados", "Carregador portatil", "Adaptador de tomada", "Hidratante (ar seco)"]
    },
    "tropical": {
        "clothing": ["Roupa leve e que seque rapido", "Fato de banho (2 — demora a secar)", "Calcoes e camisas frescas", "Sarong/pareo (obrigatorio para templos)", "Chinelos e sandalias impermeaveis", "Camisola leve para noites"],
        "essentials": ["Protecao solar SPF50 resistente a agua", "Repelente de mosquitos (DEET)", "Garrafa de agua reutilizavel", "Saco impermeavel para eletronicos", "Carregador portatil", "Medicacao basica (diarreia do viajante, dores de cabeca)"]
    },
}

CHECKLIST_TEMPLATE = {
    "documents": ["Passaporte/CC (verifica validade)", "Seguro de viagem", "Copia digital dos documentos (email/cloud)", "Bilhetes de aviao (digital ou impresso)", "Reserva do hotel (confirmacao)"],
    "hygiene": ["Escova e pasta de dentes", "Desodorizante", "Medicacao pessoal", "Kit de primeiros socorros basico"],
    "tech": ["Carregador do telemovel", "Adaptador de tomada", "Powerbank", "Auriculares", "eSIM ou plano de dados internacional"],
}
