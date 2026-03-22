import type { UseCase } from "../use-cases";

export const useCasesNl: Record<string, UseCase> = {
  legal: {
    slug: "legal",
    badge: "Juridisch",
    heroTitle: "Stop met contracten lezen.<br>Begin ze te bevragen.",
    heroSubtitle: "Bekijk complete contractportfolio's in minuten. Elke clausule geciteerd tot de exacte zin — klik om te verifiëren op de originele pagina.",
    painPoints: [
      {
        title: "Contractreview duurt weken",
        desc: "Juridisch assistenten lezen handmatig honderden contracten op zoek naar specifieke clausules. Eén portfolioreview kan 6 tot 12 weken duren.",
      },
      {
        title: "Ctrl+F mist wat belangrijk is",
        desc: "\"Wijziging van zeggenschap\" kan geschreven zijn als \"overdracht van eigendom\", \"cessie van rechten\" of begraven in een definitiesectie. Zoeken op trefwoord vindt niet wat het niet kan voorspellen.",
      },
      {
        title: "AI-samenvattingen die je niet kunt citeren",
        desc: "ChatGPT vat je contract samen — maar als de tegenpartij vraagt \"waar staat dat?\", ben je terug bij handmatig zoeken.",
      },
      {
        title: "Kruisverwijzingen zijn foutgevoelig",
        desc: "De raamovereenkomst zegt het ene, het addendum het andere, en de side letter spreekt beide tegen. Deze inconsistenties handmatig vinden is waar fouten ontstaan.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Stel vragen over je hele portfolio",
        desc: "Upload 500 contracten. Stel één vraag. Evidoc vindt elke relevante clausule in elk document — geciteerd tot de exacte zin.",
      },
      {
        title: "Klik op een citaat om te verifiëren",
        desc: "Elk antwoord bevat genummerde citaten. Klik er op — de originele PDF opent met de exacte zin gemarkeerd. Verificatie in seconden, niet uren.",
      },
      {
        title: "Detecteert inconsistenties automatisch",
        desc: "\"Komen de addendumvoorwaarden overeen met de raamovereenkomst?\" Evidoc kruisverwijst beide documenten en citeert elke afwijking.",
      },
      {
        title: "Begrijpt juridische taal",
        desc: "\"Acme Corp\", \"Acme Corporation\" en \"de Verkoper\" — Evidoc koppelt ze automatisch. Het leest als een jurist, niet als een zoekmachine.",
      },
    ],
    exampleQueries: [
      { question: "Welke contracten hebben een change-of-control clausule?", context: "Over een portfolio van 200 contracten — elke relevante clausule in seconden geciteerd." },
      { question: "Wat zijn de opzeggingsbepalingen in het Acme-contract?", context: "Elke opzeggingsgerelateerde clausule, inclusief die in addenda en side letters." },
      { question: "Verschillen de vrijwaringsvoorwaarden tussen de VS- en EU-contracten?", context: "Vergelijking tussen documenten met geciteerde verschillen uit beide versies." },
      { question: "Welke contracten verlopen in de komende 90 dagen?", context: "Datumextractie uit alle documenten met links naar de exacte clausule." },
      { question: "Zijn er concurrentiebedingen die na beëindiging doorlopen?", context: "Vindt overlevingsclausules, ook als ze anders geformuleerd zijn in verschillende overeenkomsten." },
    ],
    testimonial: {
      quote: "We waren 3 dagen bezig met het kruisverwijzen van contracten. Nu stellen we één vraag en krijgen elke relevante clausule — geciteerd tot de exacte zin.",
      author: "Early Access-gebruiker, Juridische Operaties",
    },
    ctaText: "Probeer Evidoc Gratis voor Juridisch",
  },

  finance: {
    slug: "finance",
    badge: "Financiën & Inkoop",
    heroTitle: "Elke factuur gecontroleerd.<br>Elke afwijking geciteerd.",
    heroSubtitle: "Vergelijk facturen met contracten, vind overcharges en bereid auditreacties voor — met klikbaar bewijs.",
    painPoints: [
      {
        title: "Factuurcontrole is handwerk",
        desc: "Inkoopteams vergelijken facturen regel voor regel met contracten. Bij 500+ facturen per maand glippen overcharges erdoor — gemiddeld $230.000 per jaar.",
      },
      {
        title: "Auditors willen bewijs, geen samenvattingen",
        desc: "Als de auditor vraagt \"waar staat dat het tarief $150/uur is?\", heb je de exacte clausule nodig — geen ChatGPT-samenvatting.",
      },
      {
        title: "Financiële gegevens staan in tientallen documenten",
        desc: "Het contract, de addenda, de inkooporders, de facturen, de creditnota's — het antwoord is verspreid over 20 documenten in 3 verschillende formaten.",
      },
      {
        title: "De maandafsluiting duurt te lang",
        desc: "Financiële gegevens reconciliëren, kosten verifiëren en documentatie voorbereiden — het is nauwkeurig maar pijnlijk traag.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Vergelijk facturen en contracten direct",
        desc: "\"Komen deze facturen overeen met de afgesproken contracttarieven?\" Upload beide — Evidoc citeert elke afwijking met het exacte tarief uit elk document.",
      },
      {
        title: "Audit-ready antwoorden in seconden",
        desc: "Elk antwoord is traceerbaar naar de bron. Als de auditor vraagt, klik je op het citaat — het originele document opent met de relevante zin gemarkeerd.",
      },
      {
        title: "Kruisverwijzingen over documenttypen",
        desc: "Contracten, addenda, inkooporders, facturen, creditnota's — Evidoc verbindt ze allemaal. Eén vraag bestrijkt alles.",
      },
      {
        title: "Vangt wat mensen missen",
        desc: "\"Acme\" op de factuur en \"ACME Corporation\" in het contract? Dezelfde entiteit, automatisch gekoppeld. Tariefwijziging in addendum #3? Gevonden en geciteerd.",
      },
    ],
    exampleQueries: [
      { question: "Komen deze facturen overeen met de contractvoorwaarden?", context: "Elk tarief, elke hoeveelheid en elke voorwaarde vergeleken — afwijkingen geciteerd uit beide documenten." },
      { question: "Wat is het afgesproken uurtarief voor noodreparaties?", context: "Vindt de exacte clausule, ook als het tarief in een addendum is gewijzigd." },
      { question: "Welke facturen overschrijden het goedgekeurde budget?", context: "Kruisverwijst inkooporderbedragen tegen factuurtotalen met geciteerde bronnen." },
      { question: "Wat zijn de betalingsvoorwaarden voor alle leverancierscontracten?", context: "Net 30, Net 60, kortingen voor vroege betaling — alles geëxtraheerd en geciteerd." },
      { question: "Hebben leveranciers hun tarieven gewijzigd in de afgelopen 12 maanden?", context: "Vergelijkt originele overeenkomsten met addenda en laatste facturen." },
    ],
    ctaText: "Probeer Evidoc Gratis voor Financiën",
  },

  compliance: {
    slug: "compliance",
    badge: "Compliance & Audit",
    heroTitle: "Als de auditor vraagt,<br>antwoord in seconden.",
    heroSubtitle: "Vind precies waar je beleid elke eis adresseert — geciteerd tot de zin, gemarkeerd op de originele pagina.",
    painPoints: [
      {
        title: "Auditvoorbereiding duurt dagen",
        desc: "\"Waar adresseren jullie beleidsdocumenten dataretentie?\" Het compliance-team besteedt 3 dagen aan het doorzoeken van 40+ beleidsdocumenten.",
      },
      {
        title: "Beleid is verspreid",
        desc: "Het databeleid zegt het ene, het personeelshandboek het andere, en de SOC 2-documentatie verwijst naar een derde versie. Welke is actueel?",
      },
      {
        title: "Gap-analyse is handwerk",
        desc: "Je beleid vergelijken met een nieuwe verordening betekent elk beleidsdocument lezen en vereisten handmatig mappen. Voor een team van 3 personen duurt dat weken.",
      },
      {
        title: "Compliance bewijzen vereist bewijs",
        desc: "De auditor wil geen samenvatting. Die wil de exacte beleidsformulering, de exacte versie, in het exacte document. Screenshots en handmatige markeringen zijn niet schaalbaar.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Beantwoord auditvragen direct",
        desc: "\"Waar adresseert ons beleid dataretentie?\" — Evidoc vindt elke relevante beleidsverklaring in alle documenten, geciteerd tot de exacte zin.",
      },
      {
        title: "Klikbaar bewijs voor auditors",
        desc: "Deel het antwoord met citaten. De auditor klikt — ziet de exacte zin gemarkeerd op het originele beleidsdocument. Geen heen-en-weer.",
      },
      {
        title: "Beleidsgap-analyse in minuten",
        desc: "Upload de nieuwe verordening en je bestaande beleid. Vraag \"Welke eisen worden niet gedekt door ons huidige beleid?\" — gaps geciteerd van beide kanten.",
      },
      {
        title: "Volg beleidsconsistentie",
        desc: "\"Is het personeelshandboek in lijn met ons databeleid over bewaartermijnen?\" Evidoc vindt inconsistenties en citeert beide versies.",
      },
    ],
    exampleQueries: [
      { question: "Waar adresseert ons beleid dataretentie?", context: "Elke retentie-gerelateerde clausule in alle beleidsdocumenten, met exacte citaten." },
      { question: "Welke SOP's moeten worden bijgewerkt voor de nieuwe ISO-standaard?", context: "Gap-analyse tussen huidige SOP's en de nieuwe standaard, beide kanten geciteerd." },
      { question: "Wat is onze meldtermijn bij een datalek?", context: "Vindt de meldvereisten in het privacybeleid, het incidentresponsplan en de contracten." },
      { question: "Bevatten onze leveranciersovereenkomsten dataverwerkingsclausules?", context: "Controleert alle leverancierscontracten op DPA-formuleringen en citeert aanwezige en ontbrekende clausules." },
      { question: "Welke medewerkersopleidingen zijn vereist volgens ons beleid?", context: "Extraheert alle opleidingsvereisten uit het handboek, beveiligingsbeleid en compliance-documenten." },
    ],
    testimonial: {
      quote: "Onze laatste SOC 2-auditvoorbereiding ging van 2 weken naar 2 dagen. Elke auditorvraag beantwoord met de exacte beleidsformulering, geciteerd en klikbaar.",
      author: "Early Access-gebruiker, Compliance Manager",
    },
    ctaText: "Probeer Evidoc Gratis voor Compliance",
  },

  research: {
    slug: "research",
    badge: "Onderzoek & Academie",
    heroTitle: "50 papers lezen.<br>Of ze één vraag stellen.",
    heroSubtitle: "Synthetiseer bevindingen uit onderzoekspapers, klinische studies en technische rapporten — elke claim traceerbaar naar de bron.",
    painPoints: [
      {
        title: "Literatuurstudies duren weken",
        desc: "50 papers lezen om de stand van het onderzoek te begrijpen. Markeren, notities maken, kruisverwijzen — grondig maar pijnlijk traag.",
      },
      {
        title: "Bevindingen zijn begraven in context",
        desc: "Het belangrijkste resultaat staat op pagina 14 van paper #37, maar het spreekt een bevinding op pagina 8 van paper #12 tegen. Je ontdekt dit pas na het volledig lezen van beide.",
      },
      {
        title: "Citaatopvolging is handwerk",
        desc: "Je herinnert je iets relevants gelezen te hebben maar weet niet meer welke paper. Nu lees je 20 papers opnieuw om één zin te vinden.",
      },
      {
        title: "AI-samenvattingen verliezen de nuance",
        desc: "ChatGPT vat een paper samen maar mist de kanttekeningen. \"Effectief in 80% van de gevallen\" wordt \"effectief\" — en zonder herlezen kun je dat niet verifiëren.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Stel vragen over je hele corpus",
        desc: "Upload 50 papers. Vraag \"Wat zeggen deze studies over behandeling X?\" — geconsolideerde bevindingen uit elke paper, geciteerd tot de exacte zin.",
      },
      {
        title: "Elke claim is traceerbaar",
        desc: "\"Paper 12, pagina 8, paragraaf 3\" — klik op het citaat en zie de exacte zin gemarkeerd. Geen ambiguïteit over wat de originele paper daadwerkelijk zei.",
      },
      {
        title: "Vindt tegenstrijdigheden automatisch",
        desc: "\"Zijn deze papers het oneens over de effectiviteit van methode Y?\" — Evidoc vindt tegenstrijdige bevindingen en citeert beide kanten.",
      },
      {
        title: "Werkt met alle documenttypen",
        desc: "PDF's, Word-documenten, spreadsheets met datatabellen, gescande historische papers — allemaal verbonden, allemaal doorzoekbaar, allemaal geciteerd.",
      },
    ],
    exampleQueries: [
      { question: "Wat zeggen deze papers over de werkzaamheid van behandeling X?", context: "Geconsolideerde bevindingen uit 50 papers met individuele citaten per claim." },
      { question: "Welke studies rapporteren bijwerkingen?", context: "Elke vermelding van bijwerkingen of negatieve uitkomsten — geciteerd per paper." },
      { question: "Hoe verhouden de steekproefgroottes zich tot elkaar?", context: "Extraheert methodologische details uit elke paper met geciteerde bronnen." },
      { question: "Spreken papers de bevindingen van Smith et al. 2024 tegen?", context: "Vindt tegenstrijdige conclusies en citeert de specifieke passages uit elke paper." },
      { question: "Welke onderzoekslacunes worden in deze literatuur geïdentificeerd?", context: "Compileert secties over toekomstig werk en beperkingen uit alle papers." },
    ],
    ctaText: "Probeer Evidoc Gratis voor Onderzoek",
  },

  realestate: {
    slug: "real-estate",
    badge: "Vastgoed & Onroerend Goed",
    heroTitle: "Elke clausule. Elk tegenbod.<br>Kruisgewezen.",
    heroSubtitle: "Vergelijk biedingen, bekijk huurcontracten en ontdek afwijkingen in vastgoeddocumenten — met bewijs bij elk antwoord.",
    painPoints: [
      {
        title: "Biedingsvergelijkingen zijn tijdrovend",
        desc: "Drie tegenbiedingen, elk 30 pagina's. Wat is er veranderd? Makelaars vergelijken ze handmatig, alinea voor alinea, hopend dat ze niets missen.",
      },
      {
        title: "Huurcontractportfolio's zijn onbeheersbaar",
        desc: "Een vastgoedbeheerbedrijf met 200 huurcontracten kan niet snel antwoorden op \"Welke contracten staan onderhuur toe?\" zonder elk contract te lezen.",
      },
      {
        title: "Inspectierapporten stapelen zich op",
        desc: "Jaarlijkse inspecties, onderhoudsgegevens, aannemersrapporten — ze worden opgeslagen maar nooit kruisgewezen. Patronen blijven onopgemerkt tot ze problemen worden.",
      },
      {
        title: "Due diligence is een race tegen de klok",
        desc: "Vastgoed verwerven? Milieurapporten, eigendomsdocumenten, bestemmingsplannen — alles moet beoordeeld worden onder een strak deadline.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Vergelijk documenten direct",
        desc: "Upload het oorspronkelijke bod en het tegenbod. Vraag \"Wat is er veranderd?\" — elk verschil geciteerd uit beide versies.",
      },
      {
        title: "Doorzoek je huurcontractportfolio",
        desc: "\"Welke contracten hebben een huisdierenbeleid?\" \"Wat is de gemiddelde huurescalatieclausule?\" Eén vraag over 200 contracten, elk antwoord geciteerd.",
      },
      {
        title: "Verbind onderhoudshistorie",
        desc: "Upload inspectierapporten, aannemersfacturen en serviceovereenkomsten. Vraag \"Is het HVAC-systeem onderhouden volgens de contractvoorwaarden?\"",
      },
      {
        title: "Versnel due diligence",
        desc: "Upload het volledige documentpakket. Stel vragen wanneer je wilt — elk antwoord is traceerbaar naar het brondocument. Due diligence in dagen, niet weken.",
      },
    ],
    exampleQueries: [
      { question: "Wat is er veranderd in het tegenbod?", context: "Elke herziene voorwaarde, toegevoegde clausule en verwijderde conditie — geciteerd uit beide versies." },
      { question: "Welke huurcontracten verlopen in de komende 6 maanden?", context: "Vervaldata geëxtraheerd uit alle contracten met geciteerde verlengingsvoorwaarden." },
      { question: "Signaleren de inspectierapporten terugkerende problemen?", context: "Patronen over jaren van rapporten, elke gebeurtenis geciteerd." },
      { question: "Wat zijn de servicekosten voor alle commerciële huurcontracten?", context: "Servicekostenvoorwaarden vergeleken over het hele portfolio." },
      { question: "Zijn er milieuzorgen in het due diligence-pakket?", context: "Bevindingen uit milieurapporten, onderzoeken en beoordelingen — allemaal geciteerd." },
    ],
    ctaText: "Probeer Evidoc Gratis voor Vastgoed",
  },

  personal: {
    slug: "personal",
    badge: "Persoonlijk & Dagelijks",
    heroTitle: "Je documenten,<br>eindelijk leesbaar.",
    heroSubtitle: "Verzekeringspolissen, belastingdocumenten, medische dossiers — stel een vraag in gewone taal, krijg een betrouwbaar antwoord.",
    painPoints: [
      {
        title: "Verzekeringspolissen zijn onleesbaar",
        desc: "80 pagina's juridisch jargon. Je wilt weten of je dak gedekt is, maar het antwoord is begraven in uitsluitingen, sublimieten en definities die naar andere secties verwijzen.",
      },
      {
        title: "Belastingdocumenten zijn verwarrend",
        desc: "Jaaropgaven, aftrekbewijzen — je weet dat de informatie er is, maar het specifieke bedrag vinden duurt langer dan het zou moeten.",
      },
      {
        title: "Medische dossiers zijn verspreid",
        desc: "Labresultaten van de ene arts, specialistbrieven van een andere, beeldvormingsrapporten van een derde. Een compleet beeld krijgen betekent alles lezen.",
      },
      {
        title: "Juridische overeenkomsten zijn intimiderend",
        desc: "Huurovereenkomsten, arbeidscontracten, leningsdocumenten — je hebt ze ondertekend maar weet niet helemaal zeker wat je hebt afgesproken.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Stel je vraag in gewone taal",
        desc: "\"Dekt mijn verzekering waterschade?\" — Evidoc vindt de relevante dekking, uitsluitingen en limieten, geciteerd tot de exacte polistekst.",
      },
      {
        title: "Verifieer elk antwoord",
        desc: "Neem de AI niet op zijn woord. Klik op het citaat — zie de exacte zin gemarkeerd op het originele document. Jij beslist of het klopt.",
      },
      {
        title: "Upload wat je wilt",
        desc: "PDF's, gescande documenten, foto's van papierwerk — Evidoc leest ze allemaal. 15+ formaten ondersteund.",
      },
      {
        title: "13 talen ondersteund",
        desc: "Stel je vraag in je eigen taal. Evidoc detecteert automatisch en antwoordt in dezelfde taal — met spraakinvoer voor handsfree gebruik.",
      },
    ],
    exampleQueries: [
      { question: "Wat dekt mijn verzekering eigenlijk?", context: "Dekking, uitsluitingen, eigen risico en limieten — allemaal geciteerd uit je polis." },
      { question: "Wat is mijn eigen risico voor spoedeisende hulp?", context: "Vindt het exacte bedrag met de specifieke polisclausule." },
      { question: "Mag mijn verhuurder de huur verhogen voor het einde van het contract?", context: "Huurverhogingsclausules geciteerd uit je huurovereenkomst." },
      { question: "Wat zijn de boetes voor vervroegde aflossing?", context: "Vervroegde aflossingsvoorwaarden uit je leningsovereenkomst, geciteerd tot de exacte sectie." },
      { question: "Wat heeft mijn arts aanbevolen bij het laatste bezoek?", context: "Extraheert aanbevelingen uit de bezoeknotities met exacte citaten." },
    ],
    ctaText: "Probeer Evidoc Gratis",
  },
};
