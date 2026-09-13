#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erzeugt sprachen/en.json und sprachen/pt.json.

Hier steht jeder deutsche Satz genau einmal, daneben die beiden
Übersetzungen. Das ist die Quelle — die JSON-Dateien sind nur das
Ergebnis. Wer einen Satz ändert, ändert ihn hier und lässt das Skript
noch einmal laufen.
"""
import json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Texte aus den Vorlagen: (deutsch, englisch, portugiesisch)
# ---------------------------------------------------------------------------
TEXTE = [
    # --- Navigation -------------------------------------------------------
    ('>Für wen<', '>Who for<', '>Para quem<'),
    ('>Ablauf<', '>How it works<', '>Como funciona<'),
    ('>Über mich<', '>About me<', '>Sobre mim<'),
    ('>Stimmen<', '>Voices<', '>Vozes<'),
    ('>Finanzcoaching<', '>Financial coaching<', '>Coaching financeiro<'),
    ('>Kontakt<', '>Contact<', '>Contacto<'),

    # --- Hero -------------------------------------------------------------
    ('Life &amp; Business Coaching — Düsseldorf und online',
     'Life &amp; business coaching — Düsseldorf and online',
     'Life &amp; Business Coaching — Düsseldorf e online'),
    ('Authentisch leben,<br><em>klar handeln.</em>',
     'Live authentically,<br><em>act with clarity.</em>',
     'Viver com autenticidade,<br><em>agir com clareza.</em>'),
    ('Ein geschützter Raum, in dem du dich verstanden, gesehen und getragen fühlst — und in dem du genau die Person sein darfst, die du bist.',
     'A protected space where you feel understood, seen and held — and where you are allowed to be exactly the person you are.',
     'Um espaço protegido onde te sentes compreendido, visto e amparado — e onde podes ser exatamente quem és.'),
    ('Kostenloses Erstgespräch', 'Free first conversation', 'Primeira conversa gratuita'),
    ('So arbeite ich', 'How I work', 'Como trabalho'),
    ('</b> aus {{anzahl}} Google-Rezensionen',
     '</b> from {{anzahl}} Google reviews',
     '</b> de {{anzahl}} avaliações no Google'),

    # --- Für wen ----------------------------------------------------------
    ('Für wen ich da bin', 'Who I am here for', 'Para quem estou aqui'),
    ('Ich arbeite mit Menschen, die mehr wollen.',
     'I work with people who want more.',
     'Trabalho com pessoas que querem mais.'),
    ('Mehr Sinn, mehr inneres Gleichgewicht, mehr Selbstverbindung. Nicht ein bestimmtes Geschlecht, nicht ein bestimmtes Alter, nicht eine bestimmte Lebenslage — was zählt, ist, dass du reden kannst, ohne dich zu erklären und ohne verurteilt zu werden.',
     'More meaning, more inner balance, more connection with yourself. Not a particular gender, not a particular age, not a particular situation in life — what matters is that you can speak without explaining yourself and without being judged.',
     'Mais sentido, mais equilíbrio interior, mais ligação consigo mesmo. Não um determinado género, não uma determinada idade, não uma determinada fase da vida — o que conta é que possas falar sem te justificares e sem seres julgado.'),
    ('Das ist die Rückmeldung, die ich am häufigsten bekomme: dass man sich bei mir fallen lassen darf und erzählen kann, was wirklich ist. Viele kommen wieder — weil sie spüren, dass sie sich dabei selbst näherkommen.',
     'That is the feedback I hear most often: that with me you may let go and say what is really going on. Many come back — because they feel they are getting closer to themselves.',
     'É este o retorno que mais recebo: que comigo é possível baixar a guarda e dizer o que realmente se passa. Muitos voltam — porque sentem que assim se aproximam de si próprios.'),
    ('Wie das aussieht, wenn wir zusammenarbeiten, steht hier.',
     'What working together looks like is described below.',
     'O que significa trabalharmos juntos está descrito aqui.'),

    # --- Coaching ---------------------------------------------------------
    ('Ein Raum, in dem du nicht funktionieren musst.',
     'A space where you do not have to function.',
     'Um espaço onde não tens de funcionar.'),
    ('Im Gespräch schauen wir gemeinsam auf das, was gerade wirklich in dir vorgeht. Nicht auf das, was du anderen erzählst, wenn sie fragen, wie es dir geht — sondern auf das, was darunter liegt.',
     'In conversation we look together at what is really going on inside you. Not at what you tell others when they ask how you are — but at what lies underneath.',
     'Na conversa olhamos juntos para o que se passa realmente dentro de ti. Não para aquilo que dizes aos outros quando perguntam como estás — mas para o que está por baixo.'),
    ('Du gewinnst Klarheit über deine Situation, über die Muster, die sich wiederholen, und über deine nächsten Schritte — privat wie beruflich. Ich halte einen geschützten Raum, in dem du ehrlich sein darfst, auch dir selbst gegenüber. Ich dränge dich zu nichts; das Tempo bestimmst du.',
     'You gain clarity about your situation, about the patterns that keep repeating, and about your next steps — in your private life as well as at work. I hold a protected space in which you may be honest, including with yourself. I push you towards nothing; you set the pace.',
     'Ganhas clareza sobre a tua situação, sobre os padrões que se repetem e sobre os teus próximos passos — tanto na vida pessoal como profissional. Eu seguro um espaço protegido onde podes ser honesto, também contigo mesmo. Não te empurro para nada; o ritmo é teu.'),
    ('Ein Wochenende heraus aus dem Alltag, in kleiner Gruppe. Kein Programm, das abgearbeitet wird, sondern Zeit, Stille und ein Rahmen, in dem sich etwas lösen darf.',
     'A weekend away from everyday life, in a small group. No programme to work through, but time, quiet and a setting in which something is allowed to come loose.',
     'Um fim de semana longe do quotidiano, em pequeno grupo. Não um programa a cumprir, mas tempo, silêncio e um contexto onde algo se pode soltar.'),
    ('>Wochenende · kleine Gruppe · ', '>Weekend · small group · ', '>Fim de semana · pequeno grupo · '),
    ('>Termine</a>', '>Dates</a>', '>Datas</a>'),
    ('Körperarbeit mit hnc', 'Bodywork with hnc', 'Trabalho corporal com hnc'),
    ('Nicht jeder Mensch ist über Worte erreichbar. Für alle, bei denen der Weg über den Körper führt, arbeite ich zusätzlich mit',
     'Not everyone can be reached through words. For those whose path leads through the body, I also work with',
     'Nem toda a gente se alcança através das palavras. Para quem o caminho passa pelo corpo, trabalho também com'),
    ('— manuell, mit dem Nervensystem, in der Arbeitsweise vergleichbar mit Physiotherapie oder Osteopathie.',
     '— manual work with the nervous system, comparable in approach to physiotherapy or osteopathy.',
     '— trabalho manual com o sistema nervoso, na abordagem comparável a fisioterapia ou osteopatia.'),
    ('>Einzelsitzung · {{preise.hnc_dauer}} · vor Ort · ',
     '>Single session · {{preise.hnc_dauer}} · in person · ',
     '>Sessão individual · {{preise.hnc_dauer}} · presencial · '),
    ('Coaching und hnc ersetzen keine ärztliche oder psychotherapeutische Behandlung und stellen keine Diagnosen.',
     'Coaching and hnc are not a substitute for medical or psychotherapeutic treatment and do not provide diagnoses.',
     'O coaching e o hnc não substituem tratamento médico ou psicoterapêutico e não fazem diagnósticos.'),

    # --- Ablauf -----------------------------------------------------------
    ('Wie eine Sitzung abläuft', 'How a session works', 'Como decorre uma sessão'),
    ('Du musst nichts vorbereiten.', 'You do not need to prepare anything.', 'Não precisas de preparar nada.'),
    ('Die meisten wissen vor dem ersten Termin gar nicht so genau, was auf sie zukommt. Deshalb hier vorab, wie es bei mir läuft.',
     'Most people do not really know what to expect before the first appointment. So here is how it works with me.',
     'A maioria das pessoas não sabe bem o que esperar antes da primeira sessão. Por isso, fica aqui como funciona comigo.'),
    ('Am Anfang steht ein kostenloses Erstgespräch, dreißig Minuten, telefonisch oder online. Darin erzählst du mir, worum es geht, und wir schauen gemeinsam, was du brauchst. Daraus stellen wir dann ein Paket zusammen — meistens mehrere Sitzungen über einen Zeitraum, weil sich in einem einzelnen Termin selten etwas wirklich verändert. Wie viele es werden, entscheiden wir zusammen.',
     'It starts with a free first conversation, thirty minutes, by phone or online. You tell me what it is about and we look together at what you need. From there we put together a package — usually several sessions over a period of time, because a single appointment rarely changes much. How many there will be, we decide together.',
     'Começa com uma primeira conversa gratuita, trinta minutos, por telefone ou online. Contas-me do que se trata e vemos juntos do que precisas. A partir daí montamos um pacote — normalmente várias sessões ao longo de um período, porque raramente algo muda de verdade numa única sessão. Quantas serão, decidimos em conjunto.'),
    ('Wir sehen uns in meinen Räumen in Düsseldorf, wo du in Ruhe ankommen kannst — oder online, wenn dir das lieber ist oder der Weg zu weit wäre. Was du mir erzählst, bleibt zwischen uns. Und zwischen den Terminen bin ich erreichbar, falls etwas hochkommt, das nicht bis zum nächsten Mal warten kann.',
     'We meet in my rooms in Düsseldorf, where you can arrive and settle in peace — or online, if you prefer that or the journey would be too far. What you tell me stays between us. And between appointments I am reachable, in case something comes up that cannot wait until next time.',
     'Encontramo-nos no meu espaço em Düsseldorf, onde podes chegar com calma — ou online, se preferires ou se a distância for grande. O que me contas fica entre nós. E entre as sessões estou disponível, caso surja algo que não possa esperar até à próxima.'),

    # --- Pakete -----------------------------------------------------------
    ('>Pakete<', '>Packages<', '>Pacotes<'),
    ('Was so ein Weg kostet.', 'What such a path costs.', 'Quanto custa este caminho.'),
    ('Welches Paket zu dir passt, entscheiden wir nach dem Erstgespräch gemeinsam. Damit du vorher weißt, worauf du dich einlässt, steht hier alles offen.',
     'Which package suits you we decide together after the first conversation. So that you know beforehand what you are getting into, everything is laid out here.',
     'Qual o pacote que te serve decidimos juntos depois da primeira conversa. Para que saibas de antemão no que te envolves, está tudo aqui à vista.'),

    # --- Über mich --------------------------------------------------------
    ('Wem du das erzählst', 'Who you are telling', 'A quem o contas'),
    ('Ich bin Coach geworden.', 'I became a coach.', 'Tornei-me coach.'),
    ('Nach einer erfolgreichen Karriere in der Wirtschaft und der Mitgründung mehrerer Unternehmen (Fokus Immobilien) habe ich mich bewusst für einen neuen Weg entschieden — einen Weg, der aus tiefstem Herzen kommt.',
     'After a successful career in business and co-founding several companies with a focus on real estate, I deliberately chose a new path — one that comes from the heart.',
     'Depois de uma carreira bem-sucedida na área empresarial e da cofundação de várias empresas com foco no imobiliário, escolhi conscientemente um novo caminho — um caminho que vem do coração.'),
    ('Ich wollte meinen beruflichen Lebensinhalt nicht nur über monetären Erfolg definieren. Ich wollte etwas beitragen, das sich sinnvoll und wertvoll anfühlt. Für mich ist das die Arbeit mit Menschen.',
     'I did not want to define my working life by financial success alone. I wanted to contribute something that feels meaningful and worthwhile. For me, that is working with people.',
     'Não queria definir a minha vida profissional apenas pelo sucesso financeiro. Queria contribuir com algo que se sentisse significativo e valioso. Para mim, isso é o trabalho com pessoas.'),
    ('Diese Entscheidung war keine strategische — sie war eine Herzensentscheidung. Heute begleite ich Menschen, die sich nach echter Veränderung sehnen, die ein klares, zukunftsorientiertes Ziel haben und bereit sind, ihren Weg mit neuer Klarheit, Tiefe und Selbstvertrauen zu gehen.',
     'That decision was not a strategic one — it came from the heart. Today I accompany people who long for real change, who have a clear goal ahead of them and are ready to walk their path with new clarity, depth and confidence.',
     'Essa decisão não foi estratégica — foi uma decisão do coração. Hoje acompanho pessoas que anseiam por uma mudança real, que têm um objetivo claro à sua frente e estão prontas para seguir o seu caminho com nova clareza, profundidade e confiança.'),
    ('Als zertifizierter Life &amp; Business Coach verbinde ich fundiertes Wissen mit einem feinen Gespür für das, was zwischen den Zeilen liegt. In meiner Arbeit werde ich oft als „Emotionsöffnerin" beschrieben — als jemand, der in einem geschützten Raum echte Gefühle sichtbar macht, Klarheit schafft und liebevoll Halt gibt.',
     'As a certified life &amp; business coach I combine solid knowledge with a fine sense for what lies between the lines. In my work I am often described as someone who opens up emotions — someone who makes real feelings visible in a protected space, creates clarity and offers warm support.',
     'Como coach certificada de life &amp; business, combino conhecimento sólido com uma sensibilidade fina para o que está nas entrelinhas. No meu trabalho, sou muitas vezes descrita como alguém que abre as emoções — alguém que, num espaço protegido, torna visíveis os sentimentos verdadeiros, cria clareza e dá apoio com carinho.'),
    ('Ich arbeite mit Menschen, die mehr wollen — mehr Sinn, mehr inneres Gleichgewicht, mehr Selbstverbindung. Ob es um private Themen oder berufliche Entwicklung geht: Mein Coaching ist ein Raum, in dem du dich verstanden, gesehen und getragen fühlst.',
     'I work with people who want more — more meaning, more inner balance, more connection with themselves. Whether it is about private matters or professional development: my coaching is a space in which you feel understood, seen and held.',
     'Trabalho com pessoas que querem mais — mais sentido, mais equilíbrio interior, mais ligação consigo mesmas. Quer se trate de temas pessoais ou de desenvolvimento profissional: o meu coaching é um espaço onde te sentes compreendido, visto e amparado.'),
    ('Mit Herz, Feingefühl und einem Blick für das Wesentliche begleite ich dich auf deinem Weg in deine Zukunft.',
     'With heart, sensitivity and an eye for what matters, I accompany you on your way into your future.',
     'Com coração, sensibilidade e um olhar para o essencial, acompanho-te no teu caminho para o futuro.'),
    ('Zertifizierte Life &amp; Business Coach', 'Certified life &amp; business coach', 'Coach certificada de life &amp; business'),
    ('hnc-Anwenderin — human neuro cybrainetics', 'hnc practitioner — human neuro cybrainetics', 'Praticante de hnc — human neuro cybrainetics'),
    ('Sitzungen auf Deutsch, Portugiesisch und Englisch',
     'Sessions in German, Portuguese and English',
     'Sessões em alemão, português e inglês'),
    ('Düsseldorf — Sitzungen vor Ort und online',
     'Düsseldorf — sessions in person and online',
     'Düsseldorf — sessões presenciais e online'),

    # --- Zitat, Stimmen ---------------------------------------------------
    ('Du bist kein Tropfen im Ozean. Du bist ein ganzer Ozean in einem Tropfen.',
     'You are not a drop in the ocean. You are the entire ocean in a drop.',
     'Não és uma gota no oceano. És o oceano inteiro numa gota.'),
    ('Was Menschen danach sagen', 'What people say afterwards', 'O que as pessoas dizem depois'),
    ('<blockquote class="leadquote">„{{stimmen.gross.zitat}}"</blockquote>',
     '<blockquote class="leadquote">“{{stimmen.gross.zitat}}”</blockquote>',
     '<blockquote class="leadquote">«{{stimmen.gross.zitat}}»</blockquote>'),
    ('</b> aus {{anzahl}} Rezensionen · ', '</b> from {{anzahl}} reviews · ', '</b> de {{anzahl}} avaliações · '),
    ('alle auf Google lesen', 'read them all on Google', 'ler todas no Google'),

    # --- Retreats ---------------------------------------------------------
    ('Ein Wochenende, das nachwirkt.', 'A weekend that stays with you.', 'Um fim de semana que fica.'),
    ('Ein paar Tage heraus aus dem Alltag, in kleiner Gruppe. Kein Programm, das abgearbeitet wird, sondern Zeit, Stille und ein Rahmen, in dem sich etwas lösen darf.',
     'A few days away from everyday life, in a small group. No programme to work through, but time, quiet and a setting in which something is allowed to come loose.',
     'Alguns dias longe do quotidiano, em pequeno grupo. Não um programa a cumprir, mas tempo, silêncio e um contexto onde algo se pode soltar.'),
    ('Auf die Liste setzen lassen', 'Join the list', 'Entrar na lista'),
    ('>Auf die Liste</a>', '>Join the list</a>', '>Entrar na lista</a>'),

    # --- Finanzblock Startseite -------------------------------------------
    ('>Außerdem<', '>Also<', '>Além disso<'),
    ('Meine Jahre in der Wirtschaft und der Aufbau mehrerer Unternehmen mit Fokus Immobilien — dieser Teil meines Weges ist nicht verschwunden. Für alle, die diese Seite ihres Lebens endlich selbst in die Hand nehmen möchten, biete ich ein eigenes Format an. Ich verkaufe nichts und empfehle keine Produkte. Ich sorge dafür, dass du verstehst, was du tust, und dass du dranbleibst.',
     'My years in business and building several companies with a focus on real estate — that part of my path has not disappeared. For everyone who finally wants to take this side of their life into their own hands, I offer a separate format. I sell nothing and recommend no products. I make sure you understand what you are doing and that you stay with it.',
     'Os meus anos no mundo empresarial e a construção de várias empresas com foco no imobiliário — essa parte do meu caminho não desapareceu. Para quem quer finalmente pegar nesta parte da sua vida, ofereço um formato próprio. Não vendo nada e não recomendo produtos. Faço com que percebas o que estás a fazer e que não desistas.'),
    ('Mehr zum Finanzcoaching', 'More about financial coaching', 'Mais sobre o coaching financeiro'),
    ('<b>Überblick schaffen</b> — Einnahmen, Ausgaben, Puffer. Ruhe statt Bauchgefühl.',
     '<b>Getting an overview</b> — income, spending, a buffer. Calm instead of guesswork.',
     '<b>Ganhar uma visão geral</b> — receitas, despesas, uma reserva. Calma em vez de intuição.'),
    ('<b>Erste Schritte</b> — sparen, anlegen, eine eigene Struktur aufbauen.',
     '<b>First steps</b> — saving, investing, building a structure of your own.',
     '<b>Primeiros passos</b> — poupar, investir, construir uma estrutura própria.'),
    ('<b>Weiterentwickeln</b> — bestehendes Vermögen ordnen und ausrichten.',
     '<b>Going further</b> — ordering existing assets and giving them direction.',
     '<b>Ir mais longe</b> — organizar o património existente e dar-lhe direção.'),

    # --- Kontakt ----------------------------------------------------------
    ('Schreib mir, wenn du spürst, dass es Zeit ist.',
     'Write to me when you feel the time has come.',
     'Escreve-me quando sentires que é altura.'),
    ('Ein erstes Gespräch verpflichtet zu nichts. Und wenn ich nicht die Richtige für dich bin, sage ich dir das offen — und nenne dir gern jemanden, der besser passt.',
     'A first conversation commits you to nothing. And if I am not the right person for you, I will say so openly — and gladly point you to someone who fits better.',
     'Uma primeira conversa não te compromete a nada. E se eu não for a pessoa certa para ti, digo-to abertamente — e indico-te de bom grado alguém que sirva melhor.'),
    ('<span>Name</span>', '<span>Name</span>', '<span>Nome</span>'),
    ('<span>E-Mail</span>', '<span>Email</span>', '<span>E-mail</span>'),
    ('<span>Worum geht es?</span>', '<span>What is it about?</span>', '<span>Do que se trata?</span>'),
    ('<span>Bitte frei lassen</span>', '<span>Please leave empty</span>', '<span>Deixar em branco</span>'),
    ('Ein paar Sätze reichen. Du musst nichts erklären, was du noch nicht erklären möchtest.',
     'A few sentences are enough. You do not have to explain anything you do not yet want to explain.',
     'Bastam algumas frases. Não tens de explicar nada que ainda não queiras explicar.'),
    ('Ich bin einverstanden, dass meine Angaben zur Bearbeitung meiner Anfrage gespeichert werden. Mehr dazu im',
     'I agree that my details may be stored in order to handle my enquiry. More on this in the',
     'Concordo que os meus dados sejam guardados para tratar o meu pedido. Mais sobre isto na'),
    ('>Datenschutz</a>', '>privacy notice</a>', '>política de privacidade</a>'),
    ('>Anfrage senden<', '>Send enquiry<', '>Enviar pedido<'),
    ('Lieber über WhatsApp', 'Rather via WhatsApp', 'Prefiro pelo WhatsApp'),
    ('Der Knopf öffnet dein E-Mail-Programm mit der fertigen Nachricht — abschicken musst du sie dort noch selbst.',
     'The button opens your email programme with the message ready to go — you still send it from there yourself.',
     'O botão abre o teu programa de e-mail com a mensagem pronta — o envio fazes tu a partir daí.'),
    ("'Anfrage über die Website — '", "'Enquiry via the website — '", "'Pedido através do site — '"),
    ("'\\n\\n--\\nName: '", "'\\n\\n--\\nName: '", "'\\n\\n--\\nNome: '"),
    ("'\\nE-Mail: '", "'\\nEmail: '", "'\\nE-mail: '"),
    ('Dein E-Mail-Programm öffnet sich mit der fertigen Nachricht.',
     'Your email programme is opening with the finished message.',
     'O teu programa de e-mail vai abrir com a mensagem pronta.'),

    # --- Fuß --------------------------------------------------------------
    ('Coaching und hnc ersetzen keine ärztliche Behandlung. Finanzcoaching ist keine Anlageberatung und keine Anlagevermittlung.',
     'Coaching and hnc are not a substitute for medical treatment. Financial coaching is not investment advice and not investment brokerage.',
     'O coaching e o hnc não substituem tratamento médico. O coaching financeiro não é consultoria nem intermediação de investimentos.'),

    # --- Bildbeschreibungen und Hinweise ----------------------------------
    ('title="Beispielpreis"', 'title="Example price"', 'title="Preço de exemplo"'),
    ('title="Platzhalter — echter Termin fehlt noch"',
     'title="Placeholder — the real date is still missing"',
     'title="Marcador — a data real ainda falta"'),
    ('alt="Andreia da Costa bei einem Workshop"',
     'alt="Andreia da Costa at a workshop"',
     'alt="Andreia da Costa num workshop"'),
    ('title="CertyCoach zertifiziert"', 'title="Certified by CertyCoach"', 'title="Certificada pela CertyCoach"'),

    # --- Finanzcoaching-Seite ---------------------------------------------
    ('Geld ist kein<br><em>Charaktertest.</em>',
     'Money is not a<br><em>character test.</em>',
     'O dinheiro não é um<br><em>teste de carácter.</em>'),
    ('Es ist ein Handwerk. Und Handwerk darf man lernen — in jedem Alter, an jedem Punkt.',
     'It is a craft. And a craft may be learned — at any age, from any starting point.',
     'É um ofício. E um ofício aprende-se — em qualquer idade, a partir de qualquer ponto.'),
    ('Warum ich das anbiete', 'Why I offer this', 'Porque ofereço isto'),
    ('Ich kenne beide Seiten von Geld.', 'I know both sides of money.', 'Conheço os dois lados do dinheiro.'),
    ('Vor meiner Arbeit als Coach habe ich Privatkunden bei einer großen deutschen Bank beraten. Ich habe gesehen, mit welchen Fragen Menschen dorthin kommen — und wie oft sie mit dem Gefühl wieder gehen, etwas nicht verstanden zu haben, das sie eigentlich hätten verstehen dürfen.',
     'Before my work as a coach I advised private clients at a large German bank. I saw the questions people bring through the door — and how often they leave with the feeling of not having understood something they should have been allowed to understand.',
     'Antes do meu trabalho como coach, aconselhei clientes particulares num grande banco alemão. Vi com que perguntas as pessoas chegam — e com que frequência saem com a sensação de não terem percebido algo que deviam ter podido perceber.'),
    ('Seit über einem Jahrzehnt baue ich außerdem mehrere Unternehmen mit Fokus Immobilien mit auf. Ich weiß also nicht nur, wie man über Vermögen spricht, sondern wie es sich anfühlt, welches aufzubauen: die Zweifel am Anfang, die langen Strecken ohne sichtbaren Fortschritt, die Entscheidungen, die man trifft, bevor man sicher ist.',
     'For more than a decade I have also been helping to build several companies with a focus on real estate. So I know not only how to talk about wealth, but how it feels to build some: the doubts at the beginning, the long stretches without visible progress, the decisions you make before you are certain.',
     'Há mais de uma década que ajudo também a construir várias empresas com foco no imobiliário. Por isso sei não só falar sobre património, mas também como é construí-lo: as dúvidas no início, os longos trechos sem progresso visível, as decisões que se tomam antes de se ter certeza.'),
    ('Was mich nicht loslässt, ist eine Beobachtung: Viele Menschen sind klug, arbeiten hart und verdienen gut — und wissen trotzdem nicht, wo ihr Geld eigentlich hingeht. Nicht aus Nachlässigkeit, sondern weil ihnen nie jemand gezeigt hat, dass sie sich das ansehen dürfen.',
     'One observation will not leave me: many people are clever, work hard and earn well — and still do not know where their money actually goes. Not out of carelessness, but because nobody ever showed them that they are allowed to look.',
     'Há uma observação que não me larga: muitas pessoas são inteligentes, trabalham muito e ganham bem — e mesmo assim não sabem para onde vai o seu dinheiro. Não por descuido, mas porque nunca ninguém lhes mostrou que podiam olhar.'),
    ('Drei Stufen', 'Three levels', 'Três níveis'),
    ('Wir fangen da an, wo du stehst.', 'We start where you are.', 'Começamos onde tu estás.'),
    ('Es gibt keinen Mindeststand, ab dem man kommen darf. Manche starten mit einem Kontoauszug, den sie seit Monaten nicht angeschaut haben. Andere haben längst ein Portfolio und wollen es endlich verstehen statt nur besitzen.',
     'There is no minimum you have to reach before you may come. Some start with a bank statement they have not looked at for months. Others have had a portfolio for years and finally want to understand it rather than merely own it.',
     'Não há um mínimo a partir do qual se possa vir. Alguns começam com um extrato bancário que não abrem há meses. Outros já têm uma carteira e querem finalmente percebê-la em vez de apenas possuí-la.'),
    ('>Stufe 1<', '>Level 1<', '>Nível 1<'),
    ('>Stufe 2<', '>Level 2<', '>Nível 2<'),
    ('>Stufe 3<', '>Level 3<', '>Nível 3<'),
    ('<h3>Überblick schaffen</h3>', '<h3>Getting an overview</h3>', '<h3>Ganhar uma visão geral</h3>'),
    ('<h3>Erste Schritte</h3>', '<h3>First steps</h3>', '<h3>Primeiros passos</h3>'),
    ('<h3>Weiterentwickeln</h3>', '<h3>Going further</h3>', '<h3>Ir mais longe</h3>'),
    ('Für alle, bei denen Geld ein diffuses Unbehagen ist. Wir schauen gemeinsam hin: Was kommt rein, was geht raus, was bleibt. Wir bauen einen Puffer auf, der dir nachts Ruhe gibt, und räumen auf, was sich angesammelt hat. Am Ende kennst du deine Zahlen — und das allein verändert erstaunlich viel.',
     'For everyone to whom money is a vague unease. We look at it together: what comes in, what goes out, what stays. We build a buffer that lets you sleep at night and clear up what has piled up. In the end you know your numbers — and that alone changes a surprising amount.',
     'Para quem o dinheiro é um desconforto difuso. Olhamos juntos: o que entra, o que sai, o que fica. Construímos uma reserva que te dá descanso à noite e arrumamos o que se acumulou. No fim conheces os teus números — e só isso muda surpreendentemente muita coisa.'),
    ('Für alle, die anfangen wollen und nicht wissen, womit. Wir klären die Grundlagen: Wie funktioniert Sparen, das mehr ist als ein Konto? Was bedeuten Zins, Zeit und Risiko wirklich? Du baust eine Struktur auf, die zu deinem Leben passt — und lernst genug, um selbst zu entscheiden, statt jemandem glauben zu müssen.',
     'For everyone who wants to begin and does not know where. We go through the basics: how does saving work when it is more than a bank account? What do interest, time and risk really mean? You build a structure that fits your life — and learn enough to decide for yourself instead of having to take someone at their word.',
     'Para quem quer começar e não sabe por onde. Esclarecemos as bases: como funciona poupar quando é mais do que uma conta? O que significam realmente juros, tempo e risco? Constróis uma estrutura que se ajusta à tua vida — e aprendes o suficiente para decidires sozinho, em vez de teres de acreditar em alguém.'),
    ('Für alle, die schon etwas aufgebaut haben. Wir ordnen, was gewachsen ist, prüfen, ob es noch zu deinen Zielen passt, und schauen auf das große Bild: Ruhestand, Kinder, Selbstständigkeit, Immobilien. Nicht, um mehr zu haben — sondern um zu wissen, wofür.',
     'For everyone who has already built something. We order what has grown, check whether it still fits your goals, and look at the bigger picture: retirement, children, self-employment, property. Not in order to have more — but to know what it is for.',
     'Para quem já construiu alguma coisa. Organizamos o que cresceu, verificamos se ainda corresponde aos teus objetivos e olhamos para o quadro geral: reforma, filhos, trabalho por conta própria, imobiliário. Não para ter mais — mas para saber para quê.'),
    ('>Wichtig<', '>Important<', '>Importante<'),
    ('Was ich ausdrücklich nicht mache.', 'What I expressly do not do.', 'O que expressamente não faço.'),
    ('Ich bin keine Anlageberaterin und keine Vermittlerin. Ich empfehle dir keine Produkte, keine Fonds, keine Versicherungen und keine einzelnen Wertpapiere. Ich verkaufe nichts und bekomme von niemandem Provision — deshalb kann ich dir auch offen sagen, wenn etwas nicht zu dir passt.',
     'I am not an investment adviser and not a broker. I recommend no products, no funds, no insurance and no individual securities. I sell nothing and receive commission from no one — which is why I can tell you openly when something does not suit you.',
     'Não sou consultora de investimentos nem intermediária. Não te recomendo produtos, fundos, seguros nem títulos individuais. Não vendo nada e não recebo comissão de ninguém — por isso posso dizer-te abertamente quando algo não te serve.'),
    ('Ich mache auch keine Steuerberatung und keine Rechtsberatung. Wenn dein Anliegen dorthin gehört, sage ich dir das und nenne dir, wenn ich kann, jemanden.',
     'Nor do I provide tax advice or legal advice. If that is where your question belongs, I will say so and, if I can, point you to someone.',
     'Também não faço consultoria fiscal nem jurídica. Se a tua questão for dessa natureza, digo-to e, se puder, indico-te alguém.'),
    ('<strong>Was ich mache:</strong>', '<strong>What I do:</strong>', '<strong>O que faço:</strong>'),
    ('Ich sorge dafür, dass du verstehst, was du tust. Dass du deine Zahlen kennst, deine Möglichkeiten einordnen kannst und dranbleibst, auch wenn es mühsam wird. Die Entscheidungen triffst du.',
     'I make sure that you understand what you are doing. That you know your numbers, can judge your options and stay with it, even when it gets tedious. The decisions are yours.',
     'Faço com que percebas o que estás a fazer. Que conheças os teus números, saibas avaliar as tuas opções e continues, mesmo quando custa. As decisões são tuas.'),
    ('>Ablauf<', '>How it works<', '>Como funciona<'),
    ('So läuft es ab.', 'How it goes.', 'Como decorre.'),
    ('>Schritt 1<', '>Step 1<', '>Passo 1<'),
    ('>Schritt 2<', '>Step 2<', '>Passo 2<'),
    ('>Schritt 3<', '>Step 3<', '>Passo 3<'),
    ('<h3>Erstgespräch</h3>', '<h3>First conversation</h3>', '<h3>Primeira conversa</h3>'),
    ('<h3>Bestandsaufnahme</h3>', '<h3>Taking stock</h3>', '<h3>Levantamento</h3>'),
    ('<h3>Umsetzung</h3>', '<h3>Putting it into practice</h3>', '<h3>Implementação</h3>'),
    ('Dreißig Minuten, kostenlos. Du erzählst, wo du stehst. Ich sage dir, welche Stufe zu dir passt — und ob ich die Richtige für dich bin.',
     'Thirty minutes, free of charge. You tell me where you stand. I tell you which level suits you — and whether I am the right person for you.',
     'Trinta minutos, gratuitos. Contas-me onde estás. Digo-te que nível te serve — e se sou a pessoa certa para ti.'),
    ('Eine ausführliche Sitzung, in der wir alles auf den Tisch legen. Danach weißt du, wo du stehst — oft zum ersten Mal seit Langem.',
     'A thorough session in which we put everything on the table. Afterwards you know where you stand — often for the first time in a long while.',
     'Uma sessão aprofundada em que pomos tudo em cima da mesa. Depois sabes onde estás — muitas vezes pela primeira vez em muito tempo.'),
    ('Wir arbeiten in Etappen, mit konkreten Schritten zwischen den Terminen. Wie viele es werden, hängt davon ab, was du vorhast.',
     'We work in stages, with concrete steps between appointments. How many there will be depends on what you have in mind.',
     'Trabalhamos por etapas, com passos concretos entre as sessões. Quantas serão depende do que tens em mente.'),
    ('>Einzelsitzung · {{preise.finanzcoaching_dauer}} · vor Ort in Düsseldorf oder online · {{preise.finanzcoaching}}<',
     '>Single session · {{preise.finanzcoaching_dauer}} · in person in Düsseldorf or online · {{preise.finanzcoaching}}<',
     '>Sessão individual · {{preise.finanzcoaching_dauer}} · presencial em Düsseldorf ou online · {{preise.finanzcoaching}}<'),
    ('Der erste Schritt ist ein Gespräch, kein Kontoauszug.',
     'The first step is a conversation, not a bank statement.',
     'O primeiro passo é uma conversa, não um extrato bancário.'),
    ('Du musst nichts vorbereiten und nichts offenlegen, bevor du weißt, ob es passt.',
     'You need to prepare nothing and disclose nothing before you know whether it fits.',
     'Não precisas de preparar nem de revelar nada antes de saberes se serve.'),
    ('Zurück zur Startseite', 'Back to the home page', 'Voltar à página inicial'),
    ('title="Beispielwert — wird gemeinsam festgelegt"',
     'title="Example figure — agreed together"',
     'title="Valor de exemplo — definido em conjunto"'),
]

# ---------------------------------------------------------------------------
# Werte aus inhalte.json: (deutsch, englisch, portugiesisch)
# ---------------------------------------------------------------------------
WERTE = [
    ('60 Minuten', '60 minutes', '60 minutos'),
    ('1 Stunde', '1 hour', '1 hora'),
    ('90 Minuten', '90 minutes', '90 minutos'),
    ('ab 590 €', 'from €590', 'a partir de 590 €'),
    ('5,0', '5.0', '5,0'),
    ('kostenlos', 'free', 'gratuito'),
    # Preise: im Englischen steht das Zeichen vorn und das Tausendertrennzeichen
    # ist ein Komma; Portugiesisch schreibt es wie Deutsch.
    ('110 €', '€110', '110 €'),
    ('120 €', '€120', '120 €'),
    ('150 €', '€150', '150 €'),
    ('320 €', '€320', '320 €'),
    ('640 €', '€640', '640 €'),
    ('1.200 €', '€1,200', '1.200 €'),

    ('Erstgespräch', 'First conversation', 'Primeira conversa'),
    ('30 Minuten · telefonisch oder online', '30 minutes · by phone or online', '30 minutos · por telefone ou online'),
    ('Wir lernen uns kennen, du erzählst mir, worum es geht, und wir schauen gemeinsam, was du brauchst.',
     'We get to know each other, you tell me what it is about, and we look together at what you need.',
     'Ficamos a conhecer-nos, contas-me do que se trata e vemos juntos do que precisas.'),

    ('Einzelsitzung', 'Single session', 'Sessão individual'),
    ('60 Minuten · vor Ort oder online', '60 minutes · in person or online', '60 minutos · presencial ou online'),
    ('Wenn gerade etwas akut ist und du kurzfristig jemanden brauchst, der mit dir daraufschaut. Ein Termin, ohne dass du dich auf mehr festlegst.',
     'When something is acute right now and you need someone to look at it with you at short notice. One appointment, without committing to more.',
     'Quando algo está urgente e precisas de alguém que olhe para isso contigo a curto prazo. Uma sessão, sem te comprometeres com mais.'),

    ('Innere Klarheit', 'Inner clarity', 'Clareza interior'),
    ('4 × 60 Minuten', '4 × 60 minutes', '4 × 60 minutos'),

    ('Reflexion und Entwicklung', 'Reflection and development', 'Reflexão e desenvolvimento'),
    ('8 × 60 Minuten', '8 × 60 minutes', '8 × 60 minutos'),

    ('Selbstbestimmte Ausrichtung', 'Finding your own direction', 'Rumo próprio'),
    ('16 × 60 Minuten', '16 × 60 minutes', '16 × 60 minutos'),

    ('Alle Pakete sind ab dem Kauf zwölf Monate lang einlösbar. Die Termine liegen so, wie es für dich passt.',
     'All packages can be redeemed for twelve months from purchase. Appointments are arranged to suit you.',
     'Todos os pacotes podem ser usados durante doze meses a partir da compra. As sessões são marcadas quando te der jeito.'),

    ('Sie hört nicht nur zu. Sie nimmt einen als ganzen Menschen wahr.',
     'She does not just listen. She sees you as a whole person.',
     'Ela não se limita a ouvir. Vê-te como pessoa inteira.'),
    ('Nico · Google-Rezension', 'Nico · Google review', 'Nico · avaliação no Google'),
    ('Von Anfang an herrschte eine sehr angenehme und ruhige Atmosphäre.',
     'From the very beginning there was a very pleasant and calm atmosphere.',
     'Desde o início houve uma atmosfera muito agradável e calma.'),
    ('Von Anfang an angenehm, professionell und gleichzeitig sehr persönlich.',
     'Pleasant and professional from the start, and at the same time very personal.',
     'Desde o início agradável, profissional e ao mesmo tempo muito pessoal.'),
    ('Themen, die mich schon seit vielen Jahren belastet haben, durfte ich endlich loslassen.',
     'Things that had weighed on me for many years I was finally able to let go of.',
     'Temas que me pesavam há muitos anos pude finalmente largar.'),

    ('Die nächsten Termine stehen noch nicht fest. Wer auf der Liste steht, erfährt es als Erstes — schreib mir einfach, dann melde ich mich, sobald ein Termin steht.',
     'The next dates are not yet fixed. Whoever is on the list hears first — just write to me and I will get in touch as soon as a date is set.',
     'As próximas datas ainda não estão definidas. Quem está na lista sabe primeiro — escreve-me e eu aviso assim que houver data.'),
]

# Die langen Paket-Beschreibungen stehen ungekürzt in inhalte.json; sie werden
# unten aus der Datei gelesen, damit hier kein Text doppelt gepflegt wird.
PAKET_TEXTE = {
    'Innere Klarheit': (
        'In these four hours it is not about concepts or techniques. It is about you arriving back with yourself.',
        'Nestas quatro horas não se trata de conceitos nem de técnicas. Trata-se de voltares a chegar a ti.'),
    'Reflexion und Entwicklung': (
        'Here it becomes deeper and clearer at the same time. We look together at what moves you inwardly, what blocks you and what wants to grow.',
        'Aqui torna-se ao mesmo tempo mais profundo e mais claro. Olhamos juntos para o que te move por dentro, o que te bloqueia e o que quer crescer.'),
    'Selbstbestimmte Ausrichtung': (
        'This is not a process of optimisation. It is a coming back to yourself. Over time a space grows in which you can find your own direction.',
        'Isto não é um processo de otimização. É um regresso a ti mesmo. Com o tempo cria-se um espaço onde podes encontrar o teu próprio rumo.'),
}

SEITEN = {
    'index': {
        'de': ('Andreia da Costa — Authentisch leben, klar handeln',
               'Life &amp; Business Coaching, hnc und Retreats in Düsseldorf. Ein Raum, in dem du gesehen wirst.'),
        'en': ('Andreia da Costa — Live authentically, act with clarity',
               'Life &amp; business coaching, hnc and retreats in Düsseldorf. A space in which you are seen.'),
        'pt': ('Andreia da Costa — Viver com autenticidade, agir com clareza',
               'Life &amp; Business Coaching, hnc e retiros em Düsseldorf. Um espaço onde és vista e ouvida.'),
    },
    'finanzcoaching': {
        'de': ('Finanzcoaching — Andreia da Costa',
               'Finanzcoaching in Düsseldorf: Überblick schaffen, erste Schritte beim Vermögensaufbau, bestehendes Vermögen ordnen. Keine Anlageberatung.'),
        'en': ('Financial coaching — Andreia da Costa',
               'Financial coaching in Düsseldorf: getting an overview, first steps in building wealth, ordering what already exists. Not investment advice.'),
        'pt': ('Coaching financeiro — Andreia da Costa',
               'Coaching financeiro em Düsseldorf: ganhar uma visão geral, primeiros passos na construção de património, organizar o que já existe. Não é consultoria de investimentos.'),
    },
}

NAMEN = {'de': 'Deutsch', 'en': 'English', 'pt': 'Português'}

# Anführungszeichen: jede Sprache setzt sie anders.
ZITAT = {'en': ['“', '”'], 'pt': ['«', '»']}


def schreibe(code, spalte):
    """spalte: 1 = englisch, 2 = portugiesisch."""
    inhalte = json.load(open(os.path.join(ROOT, 'inhalte.json'), encoding='utf-8'))
    werte = {e[0]: e[spalte] for e in WERTE}
    for p in inhalte['pakete']:
        if p['name'] in PAKET_TEXTE:
            werte[p['text']] = PAKET_TEXTE[p['name']][spalte - 1]
    daten = {
        'code': code,
        'name': NAMEN[code],
        'seiten': {s: {'titel': v[code][0], 'beschreibung': v[code][1]} for s, v in SEITEN.items()},
        'texte': {e[0]: e[spalte] for e in TEXTE},
        'werte': werte,
        'zitat': ZITAT[code],
    }
    ziel = os.path.join(ROOT, 'build', 'sprache-' + code + '.json')
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    with open(ziel, 'w', encoding='utf-8') as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
    print('geschrieben:', ziel, len(daten['texte']), 'Texte,', len(daten['werte']), 'Werte')


if __name__ == '__main__':
    schreibe('en', 1)
    schreibe('pt', 2)
