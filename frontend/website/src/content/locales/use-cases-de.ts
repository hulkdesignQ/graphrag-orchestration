import type { UseCase } from "../use-cases";

export const useCasesDe: Record<string, UseCase> = {
  legal: {
    slug: "legal",
    badge: "Recht",
    heroTitle: "Hören Sie auf, Verträge zu lesen.<br>Fangen Sie an, sie zu befragen.",
    heroSubtitle: "Prüfen Sie ganze Vertragsportfolios in Minuten. Jede Klausel bis zum exakten Satz zitiert — klicken Sie zur Verifizierung auf der Originalseite.",
    painPoints: [
      {
        title: "Vertragsprüfung dauert Wochen",
        desc: "Rechtsanwaltsgehilfen lesen manuell Hunderte von Verträgen auf der Suche nach bestimmten Klauseln. Eine einzige Portfolioprüfung kann 6–12 Wochen dauern.",
      },
      {
        title: "Ctrl+F findet nicht, was zählt",
        desc: "\"Kontrollwechsel\" kann als \"Eigentumsübertragung\", \"Rechteabtretung\" formuliert oder in einer Definitionssektion versteckt sein. Die Stichwortsuche findet nicht, was sie nicht vorhersagen kann.",
      },
      {
        title: "KI-Zusammenfassungen, die Sie nicht zitieren können",
        desc: "ChatGPT fasst Ihren Vertrag zusammen — aber wenn die Gegenseite fragt \"wo steht das?\", sind Sie zurück bei der manuellen Suche.",
      },
      {
        title: "Querverweise sind fehleranfällig",
        desc: "Der Rahmenvertrag sagt das eine, die Ergänzung das andere, und das Begleitschreiben widerspricht beiden. Diese Inkonsistenzen manuell zu finden — da passieren Fehler.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Fragen Sie über Ihr gesamtes Portfolio",
        desc: "Laden Sie 500 Verträge hoch. Stellen Sie eine Frage. Evidoc findet jede relevante Klausel in jedem Dokument — bis zum exakten Satz zitiert.",
      },
      {
        title: "Klicken Sie auf jedes Zitat zur Verifizierung",
        desc: "Jede Antwort enthält nummerierte Zitate. Klicken Sie auf eines — das Original-PDF öffnet sich mit dem exakten Satz hervorgehoben. Verifizierung in Sekunden, nicht Stunden.",
      },
      {
        title: "Erkennt Inkonsistenzen automatisch",
        desc: "\"Stimmen die Änderungsbedingungen mit dem Rahmenvertrag überein?\" Evidoc gleicht beide Dokumente ab und zitiert jede Abweichung.",
      },
      {
        title: "Versteht juristische Sprache",
        desc: "\"Acme Corp\", \"Acme Corporation\" und \"der Verkäufer\" — Evidoc verknüpft sie automatisch. Es liest wie ein Anwalt, nicht wie eine Suchmaschine.",
      },
    ],
    exampleQueries: [
      { question: "Welche Verträge haben eine Kontrollwechselklausel?", context: "Über ein 200-Verträge-Portfolio — jede relevante Klausel in Sekunden zitiert." },
      { question: "Was sind die Kündigungsbestimmungen im Acme-Vertrag?", context: "Jede kündigungsbezogene Klausel, einschließlich Ergänzungen und Begleitschreiben." },
      { question: "Unterscheiden sich die Haftungsfreistellungen zwischen den US- und EU-Verträgen?", context: "Dokumentenübergreifender Vergleich mit zitierten Unterschieden aus beiden Versionen." },
      { question: "Welche Verträge laufen in den nächsten 90 Tagen aus?", context: "Datumsextraktion über alle Dokumente mit Links zur exakten Klausel." },
      { question: "Gibt es Wettbewerbsverbote, die die Kündigung überdauern?", context: "Findet Fortbestandsklauseln, auch wenn sie in verschiedenen Vereinbarungen unterschiedlich formuliert sind." },
    ],
    testimonial: {
      quote: "Wir haben früher 3 Tage mit Vertragsquerverweisen verbracht. Jetzt stellen wir eine Frage und bekommen jede relevante Klausel — bis zum exakten Satz zitiert.",
      author: "Early-Access-Nutzer, Rechtsabteilung",
    },
    ctaText: "Evidoc kostenlos für Recht testen",
  },

  finance: {
    slug: "finance",
    badge: "Finanzen & Beschaffung",
    heroTitle: "Jede Rechnung geprüft.<br>Jede Abweichung zitiert.",
    heroSubtitle: "Vergleichen Sie Rechnungen mit Verträgen, erkennen Sie Überzahlungen und bereiten Sie Prüfungsantworten vor — mit klickbaren Belegen.",
    painPoints: [
      {
        title: "Rechnungsprüfung ist manuell",
        desc: "Beschaffungsteams vergleichen Rechnungen Zeile für Zeile mit Verträgen. Bei über 500 Rechnungen pro Monat rutschen Überzahlungen durch — durchschnittlich 230.000 $ jährlich.",
      },
      {
        title: "Prüfer wollen Belege, keine Zusammenfassungen",
        desc: "Wenn der Prüfer fragt \"wo steht, dass der Stundensatz 150 $ beträgt?\", brauchen Sie die exakte Klausel — keine ChatGPT-Zusammenfassung.",
      },
      {
        title: "Finanzdaten verteilen sich über Dutzende Dokumente",
        desc: "Der Vertrag, die Ergänzungen, die Bestellungen, die Rechnungen, die Gutschriften — die Antwort ist über 20 Dokumente in 3 verschiedenen Formaten verteilt.",
      },
      {
        title: "Der Monatsabschluss dauert zu lange",
        desc: "Finanzunterlagen abgleichen, Gebühren verifizieren und Dokumentation zur Prüfung vorbereiten — genau, aber schmerzhaft langsam.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Vergleichen Sie Rechnungen und Verträge sofort",
        desc: "\"Stimmen diese Rechnungen mit den vereinbarten Vertragssätzen überein?\" Laden Sie beides hoch — Evidoc zitiert jede Abweichung mit dem exakten Satz aus jedem Dokument.",
      },
      {
        title: "Prüfungsfertige Antworten in Sekunden",
        desc: "Jede Antwort führt zur Quelle zurück. Wenn der Prüfer fragt, klicken Sie auf das Zitat — das Originaldokument öffnet sich mit dem relevanten Satz hervorgehoben.",
      },
      {
        title: "Querverweise über Dokumenttypen hinweg",
        desc: "Verträge, Ergänzungen, Bestellungen, Rechnungen, Gutschriften — Evidoc verbindet alles. Eine Frage umfasst alles.",
      },
      {
        title: "Erkennt, was Menschen übersehen",
        desc: "\"Acme\" auf der Rechnung und \"ACME Corporation\" im Vertrag? Dieselbe Entität, automatisch verknüpft. Tarifänderung in Ergänzung #3? Gefunden und zitiert.",
      },
    ],
    exampleQueries: [
      { question: "Stimmen diese Rechnungen mit den Vertragsbedingungen überein?", context: "Jeder Satz, jede Menge und jede Bedingung verglichen — Abweichungen aus beiden Dokumenten zitiert." },
      { question: "Was ist der vereinbarte Stundensatz für Notreparaturen?", context: "Findet die exakte Klausel, auch wenn sich der Satz in einer Ergänzung geändert hat." },
      { question: "Welche Rechnungen überschreiten das genehmigte Budget?", context: "Gleicht Bestellbeträge mit Rechnungssummen ab, mit zitierten Quellen." },
      { question: "Was sind die Zahlungsbedingungen aller Lieferantenverträge?", context: "Net 30, Net 60, Skonti — alles extrahiert und zitiert." },
      { question: "Haben Lieferanten ihre Tarife in den letzten 12 Monaten geändert?", context: "Vergleicht Originalvereinbarungen mit Ergänzungen und neuesten Rechnungen." },
    ],
    ctaText: "Evidoc kostenlos für Finanzen testen",
  },

  compliance: {
    slug: "compliance",
    badge: "Compliance & Audit",
    heroTitle: "Wenn der Prüfer fragt,<br>antworten Sie in Sekunden.",
    heroSubtitle: "Finden Sie genau, wo Ihre Richtlinien jede Anforderung adressieren — bis zum Satz zitiert, auf der Originalseite hervorgehoben.",
    painPoints: [
      {
        title: "Auditvorbereitung dauert Tage",
        desc: "\"Wo behandeln Ihre Richtlinien die Datenspeicherung?\" Das Compliance-Team verbringt 3 Tage mit der Suche in über 40 Richtliniendokumenten.",
      },
      {
        title: "Richtlinien sind verstreut",
        desc: "Die Datenrichtlinie sagt das eine, das Mitarbeiterhandbuch das andere, und die SOC-2-Dokumentation verweist auf eine dritte Version. Welche ist aktuell?",
      },
      {
        title: "Gap-Analyse ist manuell",
        desc: "Ihre Richtlinien mit einer neuen Verordnung zu vergleichen bedeutet, jedes Richtliniendokument zu lesen und Anforderungen manuell zuzuordnen. Für ein 3-Personen-Team dauert das Wochen.",
      },
      {
        title: "Compliance-Nachweis braucht Belege",
        desc: "Der Prüfer will keine Zusammenfassung. Er will den exakten Richtlinientext, die exakte Version, im exakten Dokument. Screenshots und manuelle Markierungen skalieren nicht.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Beantworten Sie Prüfungsfragen sofort",
        desc: "\"Wo behandeln unsere Richtlinien die Datenspeicherung?\" — Evidoc findet jede relevante Richtlinienerklärung in allen Dokumenten, bis zum exakten Satz zitiert.",
      },
      {
        title: "Klickbare Belege für Prüfer",
        desc: "Teilen Sie die Antwort mit Zitaten. Der Prüfer klickt — sieht den exakten Satz im Original-Richtliniendokument hervorgehoben. Kein Hin und Her.",
      },
      {
        title: "Richtlinien-Gap-Analyse in Minuten",
        desc: "Laden Sie die neue Verordnung und Ihre bestehenden Richtlinien hoch. Fragen Sie \"Welche Anforderungen sind in unseren aktuellen Richtlinien nicht abgedeckt?\" — Lücken von beiden Seiten zitiert.",
      },
      {
        title: "Richtlinienkonsistenz verfolgen",
        desc: "\"Stimmt das Mitarbeiterhandbuch mit unserer Datenrichtlinie bei den Aufbewahrungsfristen überein?\" Evidoc findet Inkonsistenzen und zitiert beide Versionen.",
      },
    ],
    exampleQueries: [
      { question: "Wo behandeln unsere Richtlinien die Datenspeicherung?", context: "Jede Aufbewahrungsklausel in allen Richtliniendokumenten, mit exakten Zitaten." },
      { question: "Welche SOPs müssen für den neuen ISO-Standard aktualisiert werden?", context: "Gap-Analyse zwischen aktuellen SOPs und dem neuen Standard, mit beiden Seiten zitiert." },
      { question: "Was ist unsere Meldefrist bei Datenschutzverletzungen?", context: "Findet die Meldeanforderungen in Datenschutzrichtlinie, Incident-Response-Plan und Verträgen." },
      { question: "Enthalten unsere Lieferantenverträge Datenverarbeitungsklauseln?", context: "Prüft alle Lieferantenverträge auf DPA-Formulierungen und zitiert vorhandene und fehlende Klauseln." },
      { question: "Welche Mitarbeiterschulungen verlangen unsere Richtlinien?", context: "Extrahiert alle Schulungsanforderungen aus Handbuch, Sicherheitsrichtlinie und Compliance-Dokumenten." },
    ],
    testimonial: {
      quote: "Unsere letzte SOC-2-Auditvorbereitung wurde von 2 Wochen auf 2 Tage verkürzt. Jede Prüferfrage mit dem exakten Richtlinientext beantwortet, zitiert und klickbar.",
      author: "Early-Access-Nutzer, Compliance-Manager",
    },
    ctaText: "Evidoc kostenlos für Compliance testen",
  },

  research: {
    slug: "research",
    badge: "Forschung & Wissenschaft",
    heroTitle: "50 Artikel lesen.<br>Oder ihnen eine Frage stellen.",
    heroSubtitle: "Synthetisieren Sie Ergebnisse aus Forschungsartikeln, klinischen Studien und technischen Berichten — jede Behauptung bis zur Quelle nachverfolgbar.",
    painPoints: [
      {
        title: "Literaturrecherchen dauern Wochen",
        desc: "50 Artikel lesen, um den Forschungsstand zu einem Thema zu verstehen. Hervorheben, Notizen machen, Querverweise erstellen — gründlich, aber schmerzhaft langsam.",
      },
      {
        title: "Ergebnisse sind im Kontext vergraben",
        desc: "Das Schlüsselergebnis steht auf Seite 14 von Artikel #37, widerspricht aber einem Ergebnis auf Seite 8 von Artikel #12. Sie entdecken dies erst, nachdem Sie beide vollständig gelesen haben.",
      },
      {
        title: "Zitatverfolgung ist manuell",
        desc: "Sie erinnern sich, etwas Relevantes gelesen zu haben, wissen aber nicht mehr in welchem Artikel. Jetzt lesen Sie 20 Artikel erneut, um einen Satz zu finden.",
      },
      {
        title: "KI-Zusammenfassungen verlieren die Nuancen",
        desc: "ChatGPT fasst einen Artikel zusammen, übersieht aber die Einschränkungen. \"In 80 % der Fälle wirksam\" wird zu \"wirksam\" — und ohne Nachlesen können Sie das nicht überprüfen.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Fragen Sie über Ihren gesamten Korpus",
        desc: "Laden Sie 50 Artikel hoch. Fragen Sie \"Was sagen diese Studien über Behandlung X?\" — konsolidierte Ergebnisse aus jedem Artikel, bis zum exakten Satz zitiert.",
      },
      {
        title: "Jede Behauptung ist nachverfolgbar",
        desc: "\"Artikel 12, Seite 8, Absatz 3\" — klicken Sie auf das Zitat und sehen Sie den exakten Satz hervorgehoben. Keine Mehrdeutigkeit darüber, was der Originalartikel tatsächlich sagte.",
      },
      {
        title: "Findet Widersprüche automatisch",
        desc: "\"Sind sich diese Artikel über die Wirksamkeit von Methode Y uneinig?\" — Evidoc findet widersprüchliche Ergebnisse und zitiert beide Seiten.",
      },
      {
        title: "Funktioniert mit allen Dokumenttypen",
        desc: "PDFs, Word-Dokumente, Tabellen mit Datentabellen, gescannte historische Artikel — alle verbunden, alle durchsuchbar, alle zitiert.",
      },
    ],
    exampleQueries: [
      { question: "Was sagen diese Artikel über die Wirksamkeit von Behandlung X?", context: "Konsolidierte Ergebnisse aus 50 Artikeln mit individuellen Zitaten für jede Behauptung." },
      { question: "Welche Studien berichten über Nebenwirkungen?", context: "Jede Erwähnung von Nebenwirkungen oder negativen Ergebnissen — pro Artikel zitiert." },
      { question: "Wie vergleichen sich die Stichprobengrößen dieser Studien?", context: "Extrahiert Methodikdetails aus jedem Artikel mit zitierten Quellen." },
      { question: "Widersprechen Artikel den Ergebnissen von Smith et al. 2024?", context: "Findet widersprüchliche Schlussfolgerungen und zitiert die spezifischen Passagen aus jedem Artikel." },
      { question: "Welche Forschungslücken werden in dieser Literatur identifiziert?", context: "Kompiliert Abschnitte zu zukünftiger Arbeit und Einschränkungen aus allen Artikeln." },
    ],
    ctaText: "Evidoc kostenlos für Forschung testen",
  },

  realestate: {
    slug: "real-estate",
    badge: "Immobilien & Grundbesitz",
    heroTitle: "Jede Klausel. Jedes Gegenangebot.<br>Querverwiesen.",
    heroSubtitle: "Vergleichen Sie Angebote, prüfen Sie Mietverträge und erkennen Sie Unstimmigkeiten in Immobiliendokumenten — mit Nachweis bei jeder Antwort.",
    painPoints: [
      {
        title: "Angebotsvergleiche sind mühsam",
        desc: "Drei Gegenangebote, je 30 Seiten. Was hat sich geändert? Makler vergleichen sie manuell, Absatz für Absatz, in der Hoffnung, keinen geänderten Begriff zu übersehen.",
      },
      {
        title: "Mietvertragsportfolios sind unüberschaubar",
        desc: "Eine Hausverwaltung mit 200 Mietverträgen kann nicht schnell beantworten \"Welche Verträge erlauben Untervermietung?\" ohne jeden einzelnen zu lesen.",
      },
      {
        title: "Inspektionsberichte stapeln sich",
        desc: "Jährliche Inspektionen, Wartungsprotokolle, Handwerkerberichte — abgelegt, aber nie querverwiesen. Muster bleiben unbemerkt, bis sie zu Problemen werden.",
      },
      {
        title: "Due Diligence ist ein Zeitdruck",
        desc: "Immobilie erwerben? Umweltberichte, Eigentumsdokumente, Bebauungsunterlagen, Mietvertragsauszüge — alles muss unter engem Zeitrahmen geprüft werden.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Vergleichen Sie Dokumente sofort",
        desc: "Laden Sie das Originalangebot und das Gegenangebot hoch. Fragen Sie \"Was hat sich geändert?\" — jeder Unterschied aus beiden Versionen zitiert.",
      },
      {
        title: "Durchsuchen Sie Ihr Mietvertragsportfolio",
        desc: "\"Welche Verträge haben eine Haustierregelung?\" \"Wie hoch ist die durchschnittliche Mietanpassungsklausel?\" Eine Frage über 200 Verträge, jede Antwort zitiert.",
      },
      {
        title: "Verbinden Sie die Wartungshistorie",
        desc: "Laden Sie Inspektionsberichte, Handwerkerrechnungen und Serviceverträge hoch. Fragen Sie \"Wurde die Klimaanlage gemäß den Vertragsbedingungen gewartet?\"",
      },
      {
        title: "Beschleunigen Sie die Due Diligence",
        desc: "Laden Sie das gesamte Dokumentenpaket hoch. Stellen Sie Fragen, wie sie aufkommen — jede Antwort führt zum Quelldokument zurück. Due Diligence in Tagen, nicht Wochen.",
      },
    ],
    exampleQueries: [
      { question: "Was hat sich im Gegenangebot geändert?", context: "Jeder geänderte Begriff, jede hinzugefügte Klausel und jede gestrichene Bedingung — aus beiden Versionen zitiert." },
      { question: "Welche Mietverträge laufen in den nächsten 6 Monaten aus?", context: "Ablaufdaten aus allen Verträgen extrahiert, mit zitierten Verlängerungsbedingungen." },
      { question: "Weisen die Inspektionsberichte auf wiederkehrende Probleme hin?", context: "Muster über Jahre von Berichten, jedes Vorkommen zitiert." },
      { question: "Wie hoch sind die Nebenkosten in allen Gewerbemietverträgen?", context: "Nebenkostenregelungen im gesamten Portfolio verglichen." },
      { question: "Gibt es Umweltbedenken im Due-Diligence-Paket?", context: "Ergebnisse aus Umweltberichten, Gutachten und Bewertungen — alle zitiert." },
    ],
    ctaText: "Evidoc kostenlos für Immobilien testen",
  },

  personal: {
    slug: "personal",
    badge: "Privat & Alltag",
    heroTitle: "Ihre Dokumente,<br>endlich verständlich.",
    heroSubtitle: "Versicherungspolicen, Steuerunterlagen, Krankenakten — stellen Sie eine Frage in einfacher Sprache, erhalten Sie eine vertrauenswürdige Antwort.",
    painPoints: [
      {
        title: "Versicherungspolicen sind unlesbar",
        desc: "80 Seiten Juristendeutsch. Sie müssen wissen, ob Ihr Dach versichert ist, aber die Antwort steckt in Ausschlüssen, Sublimits und definierten Begriffen, die auf andere Abschnitte verweisen.",
      },
      {
        title: "Steuerunterlagen sind verwirrend",
        desc: "Lohnsteuerbescheinigungen, Einnahmebelege, Abzugsquittungen — die Information ist da, aber die richtige Zahl zu finden dauert länger als nötig.",
      },
      {
        title: "Krankenakten sind verstreut",
        desc: "Laborergebnisse von einem Arzt, Facharztbriefe von einem anderen, Bildgebungsberichte von einem dritten. Ein vollständiges Bild erfordert, alles zu lesen.",
      },
      {
        title: "Rechtliche Vereinbarungen sind einschüchternd",
        desc: "Mietverträge, Arbeitsverträge, Kreditunterlagen — Sie haben sie unterschrieben, sind sich aber nicht ganz sicher, was Sie zugestimmt haben.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Fragen Sie in einfacher Sprache",
        desc: "\"Deckt meine Versicherung Wasserschäden?\" — Evidoc findet die relevante Deckung, Ausschlüsse und Limits, bis zum exakten Policentext zitiert.",
      },
      {
        title: "Überprüfen Sie jede Antwort",
        desc: "Vertrauen Sie nicht nur der KI. Klicken Sie auf das Zitat — sehen Sie den exakten Satz im Originaldokument hervorgehoben. Sie entscheiden, ob es stimmt.",
      },
      {
        title: "Laden Sie alles hoch",
        desc: "PDFs, gescannte Dokumente, Fotos von Unterlagen — Evidoc liest alles. Über 15 Formate unterstützt.",
      },
      {
        title: "13 Sprachen unterstützt",
        desc: "Fragen Sie in Ihrer Sprache. Evidoc erkennt automatisch und antwortet entsprechend — mit Spracheingabe für freihändige Nutzung.",
      },
    ],
    exampleQueries: [
      { question: "Was deckt meine Versicherung tatsächlich ab?", context: "Deckung, Ausschlüsse, Selbstbeteiligungen und Limits — alles aus Ihrer Police zitiert." },
      { question: "Wie hoch ist meine Selbstbeteiligung bei Notaufnahmebesuchen?", context: "Findet den exakten Betrag mit der spezifischen Policenklausel." },
      { question: "Kann mein Vermieter die Miete vor Vertragsende erhöhen?", context: "Mietanpassungsklauseln aus Ihrem Mietvertrag zitiert." },
      { question: "Welche Strafen gibt es bei vorzeitiger Kreditrückzahlung?", context: "Vorfälligkeitsbedingungen aus Ihrem Kreditvertrag, bis zum exakten Abschnitt zitiert." },
      { question: "Was hat mein Arzt beim letzten Besuch empfohlen?", context: "Extrahiert Empfehlungen aus den Besuchsnotizen mit exakten Zitaten." },
    ],
    ctaText: "Evidoc kostenlos testen",
  },
};
