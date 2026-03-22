import type { UseCase } from "../use-cases";

export const useCasesPl: Record<string, UseCase> = {
  legal: {
    slug: "legal",
    badge: "Prawo",
    heroTitle: "Przestań czytać umowy.<br>Zacznij je pytać.",
    heroSubtitle: "Przeglądaj całe portfele umów w kilka minut. Każda klauzula cytowana do dokładnego zdania — kliknij, aby zweryfikować na oryginalnej stronie.",
    painPoints: [
      {
        title: "Przegląd umów trwa tygodniami",
        desc: "Asystenci prawni ręcznie czytają setki umów, szukając konkretnych klauzul. Pojedynczy przegląd portfela może zająć od 6 do 12 tygodni.",
      },
      {
        title: "Ctrl+F pomija to, co ważne",
        desc: "\"Zmiana kontroli\" może być zapisana jako \"przeniesienie własności\", \"cesja praw\" lub ukryta w sekcji definicji. Wyszukiwanie słów kluczowych nie znajdzie tego, czego nie może przewidzieć.",
      },
      {
        title: "Podsumowania AI, których nie możesz cytować",
        desc: "ChatGPT podsumuje twoją umowę — ale gdy pełnomocnik strony przeciwnej zapyta \"gdzie to jest napisane?\", wracasz do ręcznego szukania.",
      },
      {
        title: "Odsyłacze krzyżowe są podatne na błędy",
        desc: "Umowa ramowa mówi jedno, aneks drugie, a pismo dodatkowe zaprzecza obydwu. Ręczne znajdowanie tych niespójności to miejsce, gdzie zdarzają się błędy.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Pytaj w całym portfelu",
        desc: "Prześlij 500 umów. Zadaj jedno pytanie. Evidoc znajdzie każdą odpowiednią klauzulę w każdym dokumencie — cytowaną do dokładnego zdania.",
      },
      {
        title: "Kliknij dowolny cytat, aby zweryfikować",
        desc: "Każda odpowiedź zawiera numerowane cytaty. Kliknij jeden — oryginalny PDF otworzy się z podświetlonym dokładnym zdaniem. Weryfikacja w sekundach, nie godzinach.",
      },
      {
        title: "Wykrywa niespójności automatycznie",
        desc: "\"Czy warunki aneksu zgadzają się z umową ramową?\" Evidoc porównuje oba dokumenty i cytuje każdą rozbieżność.",
      },
      {
        title: "Rozumie język prawniczy",
        desc: "\"Acme Corp\", \"Acme Corporation\" i \"Sprzedający\" — Evidoc łączy je automatycznie. Czyta jak prawnik, nie jak wyszukiwarka.",
      },
    ],
    exampleQueries: [
      { question: "Które umowy mają klauzulę zmiany kontroli?", context: "W portfelu 200 umów — każda odpowiednia klauzula cytowana w sekundach." },
      { question: "Jakie są postanowienia dotyczące rozwiązania umowy Acme?", context: "Każda klauzula związana z rozwiązaniem, w tym te w aneksach i pismach dodatkowych." },
      { question: "Czy warunki odszkodowawcze różnią się między umowami z USA i UE?", context: "Porównanie między dokumentami z cytowanymi różnicami z obu wersji." },
      { question: "Które umowy wygasają w ciągu najbliższych 90 dni?", context: "Ekstrakcja dat ze wszystkich dokumentów z linkami do dokładnej klauzuli." },
      { question: "Czy istnieją zobowiązania o zakazie konkurencji, które przetrwają rozwiązanie umowy?", context: "Znajduje klauzule przetrwania nawet gdy są inaczej sformułowane w różnych umowach." },
    ],
    testimonial: {
      quote: "Wcześniej spędzaliśmy 3 dni na odsyłaczach krzyżowych umów. Teraz zadajemy jedno pytanie i otrzymujemy każdą odpowiednią klauzulę — cytowaną do dokładnego zdania.",
      author: "Użytkownik Wczesnego Dostępu, Operacje Prawne",
    },
    ctaText: "Wypróbuj Evidoc za Darmo dla Prawa",
  },

  finance: {
    slug: "finance",
    badge: "Finanse i Zakupy",
    heroTitle: "Każda faktura sprawdzona.<br>Każda rozbieżność cytowana.",
    heroSubtitle: "Porównaj faktury z umowami, wykryj nadpłaty i przygotuj odpowiedzi audytowe — z dowodami, które możesz kliknąć.",
    painPoints: [
      {
        title: "Weryfikacja faktur jest ręczna",
        desc: "Zespoły zakupowe porównują faktury z umowami linia po linii. Przy ponad 500 fakturach miesięcznie nadpłaty prześlizgują się — kosztując średnio 230 000 $ rocznie.",
      },
      {
        title: "Audytorzy chcą dowodów, nie podsumowań",
        desc: "Kiedy audytor pyta \"gdzie jest napisane, że stawka to 150 $/godz.?\", potrzebujesz dokładnej klauzuli — nie podsumowania ChatGPT.",
      },
      {
        title: "Dane finansowe rozciągają się na dziesiątki dokumentów",
        desc: "Umowa, aneksy, zamówienia, faktury, noty kredytowe — odpowiedź jest rozproszona w 20 dokumentach w 3 różnych formatach.",
      },
      {
        title: "Zamknięcie miesiąca trwa za długo",
        desc: "Uzgadnianie zapisów finansowych, weryfikacja opłat i przygotowanie dokumentacji do przeglądu — dokładne, ale boleśnie powolne.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Porównaj faktury z umowami natychmiast",
        desc: "\"Czy te faktury zgadzają się z uzgodnionymi stawkami umownymi?\" Prześlij oba — Evidoc cytuje każdą rozbieżność z dokładną stawką z każdego dokumentu.",
      },
      {
        title: "Odpowiedzi gotowe do audytu w sekundach",
        desc: "Każda odpowiedź prowadzi do źródła. Gdy audytor pyta, klikasz cytat — oryginalny dokument otwiera się z podświetlonym odpowiednim zdaniem.",
      },
      {
        title: "Odsyłacze krzyżowe między typami dokumentów",
        desc: "Umowy, aneksy, zamówienia, faktury, noty kredytowe — Evidoc łączy je wszystkie. Jedno pytanie obejmuje wszystko.",
      },
      {
        title: "Łapie to, co ludziom umyka",
        desc: "\"Acme\" na fakturze i \"ACME Corporation\" w umowie? Ten sam podmiot, połączony automatycznie. Zmiana stawki w aneksie #3? Znaleziona i cytowana.",
      },
    ],
    exampleQueries: [
      { question: "Czy te faktury zgadzają się z warunkami umowy?", context: "Każda stawka, ilość i warunek porównane — rozbieżności cytowane z obu dokumentów." },
      { question: "Jaka jest uzgodniona stawka godzinowa za naprawy awaryjne?", context: "Znajduje dokładną klauzulę, nawet jeśli stawka zmieniła się w aneksie." },
      { question: "Które faktury przekraczają zatwierdzony budżet?", context: "Porównuje kwoty zamówień z sumami faktur, ze wskazaniem cytowanych źródeł." },
      { question: "Jakie są warunki płatności we wszystkich umowach z dostawcami?", context: "Net 30, Net 60, rabaty za wcześniejszą płatność — wszystko wyodrębnione i cytowane." },
      { question: "Czy jacyś dostawcy zmienili swoje stawki w ciągu ostatnich 12 miesięcy?", context: "Porównuje oryginalne umowy z aneksami i najnowszymi fakturami." },
    ],
    ctaText: "Wypróbuj Evidoc za Darmo dla Finansów",
  },

  compliance: {
    slug: "compliance",
    badge: "Zgodność i Audyt",
    heroTitle: "Gdy audytor pyta,<br>odpowiedz w sekundach.",
    heroSubtitle: "Znajdź dokładnie, gdzie twoje polityki spełniają każdy wymóg — cytowane do zdania, podświetlone na oryginalnej stronie.",
    painPoints: [
      {
        title: "Przygotowanie do audytu trwa dni",
        desc: "\"Gdzie wasze polityki dotyczą przechowywania danych?\" Zespół compliance spędza 3 dni przeszukując ponad 40 dokumentów polityk, aby zbudować odpowiedź.",
      },
      {
        title: "Polityki są rozproszone",
        desc: "Polityka danych mówi jedno, podręcznik pracownika drugie, a dokumentacja SOC 2 odnosi się do trzeciej wersji. Która jest aktualna?",
      },
      {
        title: "Analiza luk jest ręczna",
        desc: "Porównanie polityk z nową regulacją oznacza czytanie każdego dokumentu polityki i ręczne mapowanie wymagań. Dla 3-osobowego zespołu to tygodnie.",
      },
      {
        title: "Udowodnienie zgodności wymaga dowodów",
        desc: "Audytor nie chce podsumowania. Chce dokładnego brzmienia polityki, dokładnej wersji, w dokładnym dokumencie. Zrzuty ekranu i ręczne podświetlenia się nie skalują.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Odpowiedz na pytania audytowe natychmiast",
        desc: "\"Gdzie nasze polityki dotyczą przechowywania danych?\" — Evidoc znajduje każde odpowiednie stwierdzenie polityki we wszystkich dokumentach, cytowane do dokładnego zdania.",
      },
      {
        title: "Klikalne dowody dla audytorów",
        desc: "Udostępnij odpowiedź z cytatami. Audytor klika — widzi dokładne zdanie podświetlone na oryginalnym dokumencie polityki. Bez wymiany korespondencji.",
      },
      {
        title: "Analiza luk polityk w minuty",
        desc: "Prześlij nową regulację i istniejące polityki. Zapytaj \"Które wymagania nie są objęte naszymi obecnymi politykami?\" — luki cytowane z obu stron.",
      },
      {
        title: "Śledź spójność polityk",
        desc: "\"Czy podręcznik pracownika jest zgodny z naszą polityką danych w zakresie okresów przechowywania?\" Evidoc znajduje niespójności między dokumentami i cytuje obie wersje.",
      },
    ],
    exampleQueries: [
      { question: "Gdzie nasze polityki dotyczą przechowywania danych?", context: "Każda klauzula o przechowywaniu we wszystkich dokumentach polityk, z dokładnymi cytatami." },
      { question: "Które SOP wymagają aktualizacji pod nowy standard ISO?", context: "Analiza luk między obecnymi SOP a nowym standardem, obie strony cytowane." },
      { question: "Jaki jest nasz termin powiadomienia o naruszeniu danych?", context: "Znajduje wymagania powiadomień w polityce prywatności, planie reagowania na incydenty i umowach." },
      { question: "Czy nasze umowy z dostawcami zawierają klauzule przetwarzania danych?", context: "Sprawdza wszystkie umowy z dostawcami pod kątem DPA, cytując obecne i brakujące klauzule." },
      { question: "Jakie szkolenia pracowników wymagają nasze polityki?", context: "Wyodrębnia wszystkie wymagania szkoleniowe z podręcznika, polityki bezpieczeństwa i dokumentów compliance." },
    ],
    testimonial: {
      quote: "Nasze ostatnie przygotowanie do audytu SOC 2 skróciło się z 2 tygodni do 2 dni. Każde pytanie audytora odpowiedziane dokładnym brzmieniem polityki, cytowanym i klikalnym.",
      author: "Użytkownik Wczesnego Dostępu, Menedżer Zgodności",
    },
    ctaText: "Wypróbuj Evidoc za Darmo dla Zgodności",
  },

  research: {
    slug: "research",
    badge: "Badania i Nauka",
    heroTitle: "Przeczytaj 50 artykułów.<br>Lub zadaj im jedno pytanie.",
    heroSubtitle: "Syntezuj wyniki z artykułów badawczych, badań klinicznych i raportów technicznych — każde twierdzenie można prześledzić do źródła.",
    painPoints: [
      {
        title: "Przeglądy literaturowe trwają tygodniami",
        desc: "Czytanie 50 artykułów, aby zrozumieć stan badań na dany temat. Zaznaczanie, robienie notatek, odsyłacze krzyżowe — dokładne, ale boleśnie powolne.",
      },
      {
        title: "Wyniki są ukryte w kontekście",
        desc: "Kluczowy rezultat jest na stronie 14 artykułu #37, ale zaprzecza odkryciu na stronie 8 artykułu #12. Odkrywasz to dopiero po przeczytaniu obu w całości.",
      },
      {
        title: "Śledzenie cytatów jest ręczne",
        desc: "Pamiętasz, że czytałeś coś istotnego, ale nie pamiętasz w którym artykule. Teraz ponownie czytasz 20 artykułów, żeby znaleźć jedno zdanie.",
      },
      {
        title: "Podsumowania AI tracą niuanse",
        desc: "ChatGPT podsumowuje artykuł, ale pomija zastrzeżenia. \"Skuteczne w 80% przypadków\" staje się \"skuteczne\" — i nie możesz zweryfikować bez ponownego czytania.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Pytaj w całym korpusie",
        desc: "Prześlij 50 artykułów. Zapytaj \"Co mówią te badania o leczeniu X?\" — skonsolidowane wyniki z każdego artykułu, cytowane do dokładnego zdania.",
      },
      {
        title: "Każde twierdzenie jest konfirmowalne",
        desc: "\"Artykuł 12, strona 8, akapit 3\" — kliknij cytat i zobacz podświetlone dokładne zdanie. Żadnej dwuznaczności co do tego, co oryginalny artykuł faktycznie mówił.",
      },
      {
        title: "Znajduje sprzeczności automatycznie",
        desc: "\"Czy te artykuły nie zgadzają się co do skuteczności metody Y?\" — Evidoc znajduje sprzeczne wyniki i cytuje obie strony.",
      },
      {
        title: "Działa z różnymi typami dokumentów",
        desc: "PDF, dokumenty Word, arkusze kalkulacyjne z tabelami danych, zeskanowane artykuły historyczne — wszystko połączone, wszystko przeszukiwalne, wszystko cytowane.",
      },
    ],
    exampleQueries: [
      { question: "Co mówią te artykuły o skuteczności leczenia X?", context: "Skonsolidowane wyniki z 50 artykułów z indywidualnymi cytatami dla każdego twierdzenia." },
      { question: "Które badania zgłaszają działania niepożądane?", context: "Każda wzmianka o działaniach niepożądanych lub negatywnych wynikach — cytowane per artykuł." },
      { question: "Jak wypadają porównania wielkości próby w tych badaniach?", context: "Wyodrębnia szczegóły metodologiczne z każdego artykułu z cytowanymi źródłami." },
      { question: "Czy jakieś artykuły zaprzeczają wynikom Smith et al. 2024?", context: "Znajduje sprzeczne wnioski i cytuje konkretne fragmenty z każdego artykułu." },
      { question: "Jakie luki badawcze zidentyfikowano w tej literaturze?", context: "Kompiluje sekcje dotyczące przyszłych prac i ograniczeń ze wszystkich artykułów." },
    ],
    ctaText: "Wypróbuj Evidoc za Darmo dla Badań",
  },

  realestate: {
    slug: "real-estate",
    badge: "Nieruchomości",
    heroTitle: "Każda klauzula. Każda kontrpropozycja.<br>Porównane krzyżowo.",
    heroSubtitle: "Porównuj oferty, przeglądaj umowy najmu i wykrywaj rozbieżności w dokumentach nieruchomości — z dowodem przy każdej odpowiedzi.",
    painPoints: [
      {
        title: "Porównywanie ofert jest żmudne",
        desc: "Trzy kontroferty, każda po 30 stron. Co się zmieniło? Agenci porównują je ręcznie, akapit po akapicie, mając nadzieję, że nie przeoczą zmienionego warunku.",
      },
      {
        title: "Portfele najmu są nie do opanowania",
        desc: "Firma zarządzająca nieruchomościami z 200 umowami najmu nie może szybko odpowiedzieć \"Które umowy pozwalają na podnajem?\" bez czytania każdej z nich.",
      },
      {
        title: "Raporty z inspekcji się piętrzą",
        desc: "Roczne inspekcje, rejestry konserwacji, raporty wykonawców — archiwizowane, ale nigdy nie porównywane krzyżowo. Wzorce pozostają niezauważone, aż staną się problemami.",
      },
      {
        title: "Due diligence to wyścig z czasem",
        desc: "Kupujesz nieruchomość? Raporty środowiskowe, dokumenty własnościowe, rejestry zagospodarowania — wszystko wymaga przeglądu w napiętym terminie.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Porównaj dokumenty natychmiast",
        desc: "Prześlij oryginalną ofertę i kontrofertę. Zapytaj \"Co się zmieniło?\" — każda różnica cytowana z obu wersji.",
      },
      {
        title: "Przeszukaj cały portfel najmu",
        desc: "\"Które umowy mają politykę dotyczącą zwierząt?\" \"Jaka jest średnia klauzula podwyżki czynszu?\" Jedno pytanie na 200 umów, każda odpowiedź cytowana.",
      },
      {
        title: "Połącz historię konserwacji",
        desc: "Prześlij raporty z inspekcji, faktury wykonawców i umowy serwisowe. Zapytaj \"Czy system HVAC był serwisowany zgodnie z warunkami umowy?\"",
      },
      {
        title: "Przyspiesz due diligence",
        desc: "Prześlij cały pakiet dokumentów. Zadawaj pytania w trakcie — każda odpowiedź prowadzi do dokumentu źródłowego. Due diligence w dniach, nie tygodniach.",
      },
    ],
    exampleQueries: [
      { question: "Co zmieniło się w kontrofercie?", context: "Każdy zmieniony warunek, dodana klauzula i usunięty warunek — cytowane z obu wersji." },
      { question: "Które umowy najmu wygasają w ciągu najbliższych 6 miesięcy?", context: "Daty wygaśnięcia wyodrębnione ze wszystkich umów z cytowanymi warunkami odnowienia." },
      { question: "Czy raporty z inspekcji sygnalizują powtarzające się problemy?", context: "Wzorce na przestrzeni lat raportów, każde wystąpienie cytowane." },
      { question: "Jakie są opłaty CAM we wszystkich umowach najmu komercyjnego?", context: "Warunki utrzymania części wspólnych porównane w całym portfelu." },
      { question: "Czy w pakiecie due diligence są obawy środowiskowe?", context: "Wyniki z raportów środowiskowych, badań i ocen — wszystkie cytowane." },
    ],
    ctaText: "Wypróbuj Evidoc za Darmo dla Nieruchomości",
  },

  personal: {
    slug: "personal",
    badge: "Osobiste i Codzienne",
    heroTitle: "Twoje dokumenty,<br>wreszcie czytelne.",
    heroSubtitle: "Polisy ubezpieczeniowe, dokumenty podatkowe, dokumentacja medyczna — zadaj pytanie prostym językiem, otrzymaj godną zaufania odpowiedź.",
    painPoints: [
      {
        title: "Polisy ubezpieczeniowe są nieczytelne",
        desc: "80 stron języka prawniczego. Musisz wiedzieć, czy dach jest objęty ochroną, ale odpowiedź jest ukryta w wyłączeniach, sublimitach i zdefiniowanych terminach odwołujących się do innych sekcji.",
      },
      {
        title: "Dokumenty podatkowe są zagmatwane",
        desc: "PIT, rachunki odliczeń — wiesz, że informacja tam jest, ale znalezienie konkretnej liczby zajmuje więcej czasu niż powinno.",
      },
      {
        title: "Dokumentacja medyczna jest rozproszona",
        desc: "Wyniki laboratoryjne od jednego lekarza, notatki specjalisty od innego, wyniki badań obrazowych od trzeciego. Uzyskanie pełnego obrazu wymaga przeczytania wszystkiego.",
      },
      {
        title: "Umowy prawne są onieśmielające",
        desc: "Umowy najmu, umowy o pracę, dokumenty kredytowe — podpisałeś je, ale nie jesteś do końca pewien, na co się zgodziłeś.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Pytaj prostym językiem",
        desc: "\"Czy moje ubezpieczenie pokrywa szkody wodne?\" — Evidoc znajduje odpowiedni zakres ochrony, wyłączenia i limity, cytowane do dokładnego brzmienia polisy.",
      },
      {
        title: "Zweryfikuj każdą odpowiedź",
        desc: "Nie wierz AI na słowo. Kliknij cytat — zobacz dokładne zdanie podświetlone na oryginalnym dokumencie. Ty decydujesz, czy jest poprawne.",
      },
      {
        title: "Prześlij cokolwiek",
        desc: "PDF, zeskanowane dokumenty, zdjęcia papierów — Evidoc odczyta je wszystkie. Ponad 15 obsługiwanych formatów.",
      },
      {
        title: "Obsługa 13 języków",
        desc: "Pytaj w swoim języku. Evidoc automatycznie wykrywa i odpowiada w tym samym języku — z wprowadzaniem głosowym dla wygody.",
      },
    ],
    exampleQueries: [
      { question: "Co właściwie pokrywa moje ubezpieczenie?", context: "Zakres ochrony, wyłączenia, franszyzy i limity — wszystko cytowane z twojej polisy." },
      { question: "Jaka jest moja franszyza za wizytę na izbie przyjęć?", context: "Znajduje dokładną kwotę z konkretną klauzulą polisy." },
      { question: "Czy właściciel może podnieść czynsz przed końcem umowy najmu?", context: "Klauzule podwyżki czynszu cytowane z twojej umowy najmu." },
      { question: "Jakie są kary za wcześniejszą spłatę kredytu?", context: "Warunki przedterminowej spłaty z twojej umowy kredytowej, cytowane do dokładnej sekcji." },
      { question: "Co zalecił mój lekarz podczas ostatniej wizyty?", context: "Wyodrębnia zalecenia z notatek z wizyty z dokładnymi cytatami." },
    ],
    ctaText: "Wypróbuj Evidoc za Darmo",
  },
};
