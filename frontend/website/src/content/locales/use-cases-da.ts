import type { UseCase } from "../use-cases";

export const useCasesDa: Record<string, UseCase> = {
  legal: {
    slug: "legal",
    badge: "Jura",
    heroTitle: "Stop med at læse kontrakter.<br>Begynd at spørge dem.",
    heroSubtitle: "Gennemgå hele kontraktporteføljer på få minutter. Hver klausul citeret ned til den præcise sætning — klik for at verificere på den originale side.",
    painPoints: [
      {
        title: "Kontraktgennemgang tager uger",
        desc: "Advokatassistenter læser manuelt hundredvis af kontrakter for at finde specifikke klausuler. En enkelt porteføljegennemgang kan tage 6–12 uger.",
      },
      {
        title: "Ctrl+F overser det vigtige",
        desc: "\"Kontrolskifte\" kan være skrevet som \"overdragelse af ejendomsret\", \"overdragelse af rettigheder\" eller begravet i en definitionssektion. Søgning på nøgleord finder ikke det, det ikke kan forudsige.",
      },
      {
        title: "AI-resuméer du ikke kan citere",
        desc: "ChatGPT resumerer din kontrakt — men når modpartens advokat spørger \"hvor står det?\", er du tilbage til manuel søgning.",
      },
      {
        title: "Krydshenvisninger er fejlbehæftede",
        desc: "Rammeaftalen siger ét, tillægget siger noget andet, og sidebrevet modsiger begge. At finde disse uoverensstemmelser manuelt er, hvor fejl opstår.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Stil spørgsmål på tværs af hele din portefølje",
        desc: "Upload 500 kontrakter. Stil ét spørgsmål. Evidoc finder hver relevant klausul i hvert dokument — citeret ned til den præcise sætning.",
      },
      {
        title: "Klik på et citat for at verificere",
        desc: "Hvert svar indeholder nummererede citater. Klik på ét — den originale PDF åbner med den præcise sætning fremhævet. Verificering på sekunder, ikke timer.",
      },
      {
        title: "Opdager uoverensstemmelser automatisk",
        desc: "\"Stemmer tillægsvilkårene overens med rammeaftalen?\" Evidoc krydsrefererer begge dokumenter og citerer hver afvigelse.",
      },
      {
        title: "Forstår juridisk sprog",
        desc: "\"Acme Corp\", \"Acme Corporation\" og \"Sælgeren\" — Evidoc forbinder dem automatisk. Den læser som en advokat, ikke som en søgemaskine.",
      },
    ],
    exampleQueries: [
      { question: "Hvilke kontrakter har en kontrolskifteklausul?", context: "På tværs af en portefølje med 200 kontrakter — hver relevant klausul citeret på sekunder." },
      { question: "Hvad er opsigelsesbestemmelserne i Acme-aftalen?", context: "Hver opsigelsesrelateret klausul, inklusive dem i tillæg og sidebreve." },
      { question: "Er erstatningsvilkårene forskellige mellem de amerikanske og EU-kontrakterne?", context: "Sammenligning på tværs af dokumenter med citerede forskelle fra begge versioner." },
      { question: "Hvilke kontrakter udløber inden for de næste 90 dage?", context: "Datoekstraktion fra alle dokumenter med links til den præcise klausul." },
      { question: "Er der konkurrenceklausuler, der overlever opsigelse?", context: "Finder overlevelsesklausuler, selv når de er formuleret forskelligt på tværs af aftaler." },
    ],
    testimonial: {
      quote: "Vi brugte 3 dage på at krydsreferere kontrakter. Nu stiller vi ét spørgsmål og får hver relevant klausul — citeret ned til den præcise sætning.",
      author: "Early Access-bruger, Juridiske Operationer",
    },
    ctaText: "Prøv Evidoc Gratis til Jura",
  },

  finance: {
    slug: "finance",
    badge: "Finans & Indkøb",
    heroTitle: "Hver faktura kontrolleret.<br>Hver afvigelse citeret.",
    heroSubtitle: "Sammenlign fakturaer med kontrakter, find overfaktureringer og forbered revisionssvar — med klikbart bevis.",
    painPoints: [
      {
        title: "Fakturakontrol er manuelt arbejde",
        desc: "Indkøbsteams sammenligner fakturaer med kontrakter linje for linje. Ved 500+ fakturaer om måneden slipper overfaktureringer igennem — det koster i gennemsnit $230.000 årligt.",
      },
      {
        title: "Revisorer vil have bevis, ikke resuméer",
        desc: "Når revisoren spørger \"hvor står der, at satsen er $150/time?\", har du brug for den præcise klausul — ikke et ChatGPT-resumé.",
      },
      {
        title: "Finansielle poster er spredt over mange dokumenter",
        desc: "Kontrakten, tillæggene, indkøbsordrerne, fakturaerne, kreditnotaerne — svaret er spredt over 20 dokumenter i 3 forskellige formater.",
      },
      {
        title: "Månedsafslutningen tager for lang tid",
        desc: "Afstemme finansielle poster, verificere gebyrer og forberede dokumentation til gennemgang — det er præcist men smertefuldt langsomt.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Sammenlign fakturaer og kontrakter øjeblikkeligt",
        desc: "\"Stemmer disse fakturaer overens med de aftalte kontraktsatser?\" Upload begge — Evidoc citerer hver afvigelse med den præcise sats fra hvert dokument.",
      },
      {
        title: "Revisionsklar svar på sekunder",
        desc: "Hvert svar kan spores til kilden. Når revisoren spørger, klikker du på citatet — det originale dokument åbner med den relevante sætning fremhævet.",
      },
      {
        title: "Krydsreferencer på tværs af dokumenttyper",
        desc: "Kontrakter, tillæg, indkøbsordrer, fakturaer, kreditnotaer — Evidoc forbinder dem alle. Ét spørgsmål dækker alt.",
      },
      {
        title: "Fanger det, mennesker overser",
        desc: "\"Acme\" på fakturaen og \"ACME Corporation\" i kontrakten? Samme enhed, automatisk forbundet. Satsændring i tillæg #3? Fundet og citeret.",
      },
    ],
    exampleQueries: [
      { question: "Stemmer disse fakturaer overens med kontraktvilkårene?", context: "Hver sats, mængde og vilkår sammenlignet — afvigelser citeret fra begge dokumenter." },
      { question: "Hvad er den aftalte timesats for nødreparationer?", context: "Finder den præcise klausul, selv hvis satsen er ændret i et tillæg." },
      { question: "Hvilke fakturaer overskrider det godkendte budget?", context: "Krydsrefererer indkøbsordrebeløb mod fakturatotaler med citerede kilder." },
      { question: "Hvad er betalingsvilkårene for alle leverandørkontrakter?", context: "Net 30, Net 60, rabatter for tidlig betaling — alt ekstraheret og citeret." },
      { question: "Har nogen leverandører ændret deres satser inden for de sidste 12 måneder?", context: "Sammenligner originale aftaler med tillæg og seneste fakturaer." },
    ],
    ctaText: "Prøv Evidoc Gratis til Finans",
  },

  compliance: {
    slug: "compliance",
    badge: "Compliance & Revision",
    heroTitle: "Når revisoren spørger,<br>svar på sekunder.",
    heroSubtitle: "Find præcis, hvor dine politikker adresserer ethvert krav — citeret ned til sætningen, fremhævet på den originale side.",
    painPoints: [
      {
        title: "Revisionsforberedelse tager dage",
        desc: "\"Hvor adresserer jeres politikker dataopbevaring?\" Compliance-teamet bruger 3 dage på at søge i 40+ politikdokumenter for at bygge svaret.",
      },
      {
        title: "Politikker er spredt",
        desc: "Datapolitikken siger ét, medarbejderhåndbogen noget andet, og SOC 2-dokumentationen refererer til en tredje version. Hvilken er aktuel?",
      },
      {
        title: "Gap-analyse er manuelt arbejde",
        desc: "At sammenligne dine politikker med en ny forordning betyder at læse hvert politikdokument og manuelt mappe kravene. For et team på 3 tager det uger.",
      },
      {
        title: "At bevise compliance kræver dokumentation",
        desc: "Revisoren vil ikke have et resumé. De vil have den præcise politikformulering, den præcise version, i det præcise dokument. Screenshots og manuelle markeringer skalerer ikke.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Besvar revisionsspørgsmål øjeblikkeligt",
        desc: "\"Hvor adresserer vores politikker dataopbevaring?\" — Evidoc finder hver relevant politikerklæring i alle dokumenter, citeret ned til den præcise sætning.",
      },
      {
        title: "Klikbart bevis til revisorer",
        desc: "Del svaret med citater. Revisoren klikker — ser den præcise sætning fremhævet på det originale politikdokument. Ingen frem og tilbage.",
      },
      {
        title: "Politikgap-analyse på minutter",
        desc: "Upload den nye forordning og dine eksisterende politikker. Spørg \"Hvilke krav er ikke dækket af vores nuværende politikker?\" — gaps citeret fra begge sider.",
      },
      {
        title: "Følg politikkonsistens",
        desc: "\"Er medarbejderhåndbogen i overensstemmelse med vores datapolitik om opbevaringsperioder?\" Evidoc finder uoverensstemmelser og citerer begge versioner.",
      },
    ],
    exampleQueries: [
      { question: "Hvor adresserer vores politikker dataopbevaring?", context: "Hver opbevaringsrelateret klausul i alle politikdokumenter, med præcise citater." },
      { question: "Hvilke SOP'er skal opdateres til den nye ISO-standard?", context: "Gap-analyse mellem nuværende SOP'er og den nye standard, begge sider citeret." },
      { question: "Hvad er vores tidsfrist for meddelelse ved databrud?", context: "Finder meddelelseskravene i privatlivspolitik, hændelsesresponsplan og kontrakter." },
      { question: "Indeholder vores leverandøraftaler databehandlingsklausuler?", context: "Gennemgår alle leverandørkontrakter for DPA-sprogbrug, citerer tilstedeværende og manglende klausuler." },
      { question: "Hvilken medarbejderuddannelse kræves af vores politikker?", context: "Ekstraherer alle uddannelseskrav fra håndbog, sikkerhedspolitik og compliance-dokumenter." },
    ],
    testimonial: {
      quote: "Vores seneste SOC 2-revisionsforberedelse gik fra 2 uger til 2 dage. Hvert revisorspørgsmål besvaret med den præcise politikformulering, citeret og klikbar.",
      author: "Early Access-bruger, Compliance Manager",
    },
    ctaText: "Prøv Evidoc Gratis til Compliance",
  },

  research: {
    slug: "research",
    badge: "Forskning & Akademi",
    heroTitle: "Læs 50 artikler.<br>Eller stil dem ét spørgsmål.",
    heroSubtitle: "Syntesér fund fra forskningsartikler, kliniske studier og tekniske rapporter — hvert udsagn kan spores til kilden.",
    painPoints: [
      {
        title: "Litteraturgennemgange tager uger",
        desc: "At læse 50 artikler for at forstå forskningsstatus inden for et emne. Fremhæve, tage noter, krydsreferere — grundigt men smertefuldt langsomt.",
      },
      {
        title: "Fund er begravet i kontekst",
        desc: "Nøgleresultatet er på side 14 i artikel #37, men det modsiger et fund på side 8 i artikel #12. Du opdager det først efter at have læst begge helt igennem.",
      },
      {
        title: "Citatsporing er manuelt arbejde",
        desc: "Du husker at have læst noget relevant, men kan ikke huske hvilken artikel. Nu genlæser du 20 artikler for at finde én sætning.",
      },
      {
        title: "AI-resuméer mister nuancerne",
        desc: "ChatGPT resumerer en artikel men overser forbeholdene. \"Effektiv i 80% af tilfældene\" bliver til \"effektiv\" — og du kan ikke verificere uden at genlæse.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Stil spørgsmål på tværs af hele dit korpus",
        desc: "Upload 50 artikler. Spørg \"Hvad siger disse studier om behandling X?\" — konsoliderede fund fra hver artikel, citeret ned til den præcise sætning.",
      },
      {
        title: "Hvert udsagn er sporbart",
        desc: "\"Artikel 12, side 8, afsnit 3\" — klik på citatet og se den præcise sætning fremhævet. Ingen tvetydighed om, hvad den originale artikel faktisk sagde.",
      },
      {
        title: "Finder modsigelser automatisk",
        desc: "\"Er disse artikler uenige om effektiviteten af metode Y?\" — Evidoc finder modstridende fund og citerer begge sider.",
      },
      {
        title: "Fungerer med alle dokumenttyper",
        desc: "PDF'er, Word-dokumenter, regneark med datatabeller, scannede historiske artikler — alle forbundet, alle søgbare, alle citeret.",
      },
    ],
    exampleQueries: [
      { question: "Hvad siger disse artikler om effekten af behandling X?", context: "Konsoliderede fund fra 50 artikler med individuelle citater for hvert udsagn." },
      { question: "Hvilke studier rapporterer bivirkninger?", context: "Hver omtale af bivirkninger eller negative resultater — citeret per artikel." },
      { question: "Hvordan sammenligner stikprøvestørrelserne sig på tværs af disse studier?", context: "Ekstraherer metodologiske detaljer fra hver artikel med citerede kilder." },
      { question: "Modsiger nogen artikler fundene fra Smith et al. 2024?", context: "Finder modstridende konklusioner og citerer de specifikke passager fra hver artikel." },
      { question: "Hvilke forskningshuller identificeres i denne litteratur?", context: "Kompilerer sektioner om fremtidigt arbejde og begrænsninger fra alle artikler." },
    ],
    ctaText: "Prøv Evidoc Gratis til Forskning",
  },

  realestate: {
    slug: "real-estate",
    badge: "Ejendomme & Fast Ejendom",
    heroTitle: "Hver klausul. Hvert modtilbud.<br>Krydsrefereret.",
    heroSubtitle: "Sammenlign tilbud, gennemgå lejekontrakter og find afvigelser i ejendomsdokumenter — med bevis ved hvert svar.",
    painPoints: [
      {
        title: "Tilbudssammenligninger er tidskrævende",
        desc: "Tre modtilbud, hvert på 30 sider. Hvad er ændret? Mæglere sammenligner dem manuelt, afsnit for afsnit, i håb om ikke at overse et revideret vilkår.",
      },
      {
        title: "Lejekontraktporteføljer er uoverskuelige",
        desc: "Et ejendomsadministrationsselskab med 200 lejekontrakter kan ikke hurtigt svare på \"Hvilke lejekontrakter tillader fremleje?\" uden at læse dem alle.",
      },
      {
        title: "Inspektionsrapporter hober sig op",
        desc: "Årlige inspektioner, vedligeholdelsesregistreringer, entreprenørrapporter — de arkiveres men krydsrefereres aldrig. Mønstre forbliver ubemærkede, til de bliver problemer.",
      },
      {
        title: "Due diligence er en kamp mod uret",
        desc: "Købe en ejendom? Miljørapporter, skødedokumenter, zonelægningsregistreringer — alt skal gennemgås under en stram deadline.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Sammenlign dokumenter øjeblikkeligt",
        desc: "Upload det oprindelige tilbud og modtilbuddet. Spørg \"Hvad er ændret?\" — hver forskel citeret fra begge versioner.",
      },
      {
        title: "Søg på tværs af din lejekontraktportefølje",
        desc: "\"Hvilke kontrakter har en kæledyrspolitik?\" \"Hvad er den gennemsnitlige lejeeskaleringsklausul?\" Ét spørgsmål på tværs af 200 kontrakter, hvert svar citeret.",
      },
      {
        title: "Forbind vedligeholdelseshistorik",
        desc: "Upload inspektionsrapporter, entreprenørfakturaer og serviceaftaler. Spørg \"Er HVAC-systemet blevet serviceret i henhold til kontraktvilkårene?\"",
      },
      {
        title: "Fremskynd due diligence",
        desc: "Upload hele dokumentpakken. Stil spørgsmål undervejs — hvert svar kan spores til kildedokumentet. Due diligence på dage, ikke uger.",
      },
    ],
    exampleQueries: [
      { question: "Hvad er ændret i modtilbuddet?", context: "Hvert revideret vilkår, tilføjet klausul og fjernet betingelse — citeret fra begge versioner." },
      { question: "Hvilke lejekontrakter udløber inden for de næste 6 måneder?", context: "Udløbsdatoer ekstraheret fra alle kontrakter med citerede forlængelsesvilkår." },
      { question: "Peger inspektionsrapporterne på tilbagevendende problemer?", context: "Mønstre på tværs af årevis af rapporter, hvert tilfælde citeret." },
      { question: "Hvad er fællesomkostningerne for alle erhvervslejekontrakter?", context: "Fællesomkostningsvilkår sammenlignet på tværs af porteføljen." },
      { question: "Er der miljømæssige bekymringer i due diligence-pakken?", context: "Fund fra miljørapporter, undersøgelser og vurderinger — alle citeret." },
    ],
    ctaText: "Prøv Evidoc Gratis til Ejendomme",
  },

  personal: {
    slug: "personal",
    badge: "Personligt & Hverdags",
    heroTitle: "Dine dokumenter,<br>endelig læsbare.",
    heroSubtitle: "Forsikringspolicer, skattedokumenter, lægejournaler — stil et spørgsmål i dagligdags sprog, få et svar du kan stole på.",
    painPoints: [
      {
        title: "Forsikringspolicer er ulæselige",
        desc: "80 sider juridisk sprog. Du skal vide, om dit tag er dækket, men svaret er begravet i undtagelser, sublimits og definerede termer, der refererer til andre sektioner.",
      },
      {
        title: "Skattedokumenter er forvirrende",
        desc: "Årsopgørelser, fradragskvitteringer — du ved, informationen er der, men at finde det specifikke tal tager længere tid end det burde.",
      },
      {
        title: "Lægejournaler er spredt",
        desc: "Laboratorieresultater fra én læge, specialistnotater fra en anden, billeddiagnostik fra en tredje. At få et samlet billede kræver at læse alt.",
      },
      {
        title: "Juridiske aftaler er skræmmende",
        desc: "Lejekontrakter, ansættelseskontrakter, lånedokumenter — du har underskrevet dem, men er ikke helt sikker på, hvad du har sagt ja til.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Stil dit spørgsmål i dagligdags sprog",
        desc: "\"Dækker min forsikring vandskade?\" — Evidoc finder den relevante dækning, undtagelser og grænser, citeret ned til den præcise policetekst.",
      },
      {
        title: "Verificer hvert svar",
        desc: "Tag ikke AI'ens ord for det. Klik på citatet — se den præcise sætning fremhævet på det originale dokument. Du bestemmer, om det er korrekt.",
      },
      {
        title: "Upload hvad som helst",
        desc: "PDF'er, scannede dokumenter, fotos af papirer — Evidoc læser dem alle. 15+ formater understøttet.",
      },
      {
        title: "13 sprog understøttet",
        desc: "Stil dit spørgsmål på dit eget sprog. Evidoc registrerer automatisk og svarer på samme sprog — med stemmeinput til håndfri brug.",
      },
    ],
    exampleQueries: [
      { question: "Hvad dækker min forsikring egentlig?", context: "Dækning, undtagelser, selvrisiko og grænser — alt citeret fra din police." },
      { question: "Hvad er min selvrisiko for skadestuebesøg?", context: "Finder det præcise beløb med den specifikke policeklausul." },
      { question: "Kan min udlejer hæve huslejen før lejemålets udløb?", context: "Lejeforhøjelsesklausuler citeret fra din lejekontrakt." },
      { question: "Hvad er bøderne for førtidig tilbagebetaling af lån?", context: "Førtidig indfrielsesvilkår fra din låneaftale, citeret ned til den præcise sektion." },
      { question: "Hvad anbefalede min læge ved det seneste besøg?", context: "Ekstraherer anbefalinger fra besøgsnotaterne med præcise citater." },
    ],
    ctaText: "Prøv Evidoc Gratis",
  },
};
