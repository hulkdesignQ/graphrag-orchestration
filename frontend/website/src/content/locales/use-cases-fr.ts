import type { UseCase } from "../use-cases";

export const useCasesFr: Record<string, UseCase> = {
  legal: {
    slug: "legal",
    badge: "Juridique",
    heroTitle: "Arrêtez de lire les contrats.<br>Commencez à les interroger.",
    heroSubtitle: "Examinez des portefeuilles entiers de contrats en quelques minutes. Chaque clause citée jusqu'à la phrase exacte — cliquez pour vérifier sur la page originale.",
    painPoints: [
      {
        title: "La revue des contrats prend des semaines",
        desc: "Les juristes lisent manuellement des centaines de contrats à la recherche de clauses spécifiques. Une seule revue de portefeuille peut prendre 6 à 12 semaines.",
      },
      {
        title: "Ctrl+F passe à côté de l'essentiel",
        desc: "\"Changement de contrôle\" peut être formulé comme \"transfert de propriété\", \"cession de droits\" ou enfoui dans une section de définitions. La recherche par mot-clé ne trouve pas ce qu'elle ne peut pas prédire.",
      },
      {
        title: "Des résumés IA que vous ne pouvez pas citer",
        desc: "ChatGPT résumera votre contrat — mais quand l'avocat adverse demande \"où est-ce écrit ?\", vous revenez à la recherche manuelle.",
      },
      {
        title: "Les références croisées sont sujettes aux erreurs",
        desc: "Le contrat principal dit une chose, l'avenant dit autre chose, et la lettre annexe contredit les deux. Trouver ces incohérences manuellement, c'est là que les erreurs surviennent.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Interrogez l'ensemble de votre portefeuille",
        desc: "Téléchargez 500 contrats. Posez une question. Evidoc trouve chaque clause pertinente dans chaque document — citée jusqu'à la phrase exacte.",
      },
      {
        title: "Cliquez sur n'importe quelle citation pour vérifier",
        desc: "Chaque réponse inclut des citations numérotées. Cliquez sur l'une d'elles — le PDF original s'ouvre avec la phrase exacte surlignée. Vérification en secondes, pas en heures.",
      },
      {
        title: "Détectez les incohérences automatiquement",
        desc: "\"Les termes de l'avenant correspondent-ils au contrat principal ?\" Evidoc croise les deux documents et cite chaque divergence.",
      },
      {
        title: "Comprend le langage juridique",
        desc: "\"Acme Corp\", \"Acme Corporation\" et \"le Vendeur\" — Evidoc les relie automatiquement. Il lit comme un avocat, pas comme un moteur de recherche.",
      },
    ],
    exampleQueries: [
      { question: "Quels contrats contiennent une clause de changement de contrôle ?", context: "Dans un portefeuille de 200 contrats — chaque clause pertinente citée en quelques secondes." },
      { question: "Quelles sont les dispositions de résiliation dans le contrat Acme ?", context: "Chaque clause liée à la résiliation, y compris celles des avenants et lettres annexes." },
      { question: "Les conditions d'indemnisation diffèrent-elles entre les contrats américains et européens ?", context: "Comparaison inter-documents avec les différences citées des deux versions." },
      { question: "Quels contrats expirent dans les 90 prochains jours ?", context: "Extraction de dates dans tous les documents avec liens vers la clause exacte." },
      { question: "Y a-t-il des obligations de non-concurrence qui survivent à la résiliation ?", context: "Trouve les clauses de survie même lorsqu'elles sont formulées différemment d'un accord à l'autre." },
    ],
    testimonial: {
      quote: "Nous passions 3 jours à croiser les références de contrats. Maintenant, nous posons une question et obtenons chaque clause pertinente — citée jusqu'à la phrase exacte.",
      author: "Utilisateur en Accès Anticipé, Opérations Juridiques",
    },
    ctaText: "Essayez Evidoc Gratuitement pour le Juridique",
  },

  finance: {
    slug: "finance",
    badge: "Finance et Achats",
    heroTitle: "Chaque facture vérifiée.<br>Chaque écart cité.",
    heroSubtitle: "Comparez les factures aux contrats, détectez les surfacturations et préparez les réponses d'audit — avec des preuves cliquables.",
    painPoints: [
      {
        title: "La vérification des factures est manuelle",
        desc: "Les équipes achats comparent les factures aux contrats ligne par ligne. Avec plus de 500 factures par mois, les surfacturations passent entre les mailles — coûtant en moyenne 230 000 $ par an.",
      },
      {
        title: "Les auditeurs veulent des preuves, pas des résumés",
        desc: "Quand l'auditeur demande \"où est-il écrit que le taux est de 150 $/heure ?\", vous avez besoin de la clause exacte — pas d'un résumé de ChatGPT.",
      },
      {
        title: "Les registres financiers couvrent des dizaines de documents",
        desc: "Le contrat, les avenants, les bons de commande, les factures, les avoirs — la réponse est répartie sur 20 documents dans 3 formats différents.",
      },
      {
        title: "La clôture mensuelle prend trop de temps",
        desc: "Rapprocher les registres financiers, vérifier les charges et préparer la documentation pour revue — c'est précis mais terriblement lent.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Comparez factures et contrats instantanément",
        desc: "\"Ces factures correspondent-elles aux tarifs contractuels ?\" Téléchargez les deux — Evidoc cite chaque écart avec le tarif exact de chaque document.",
      },
      {
        title: "Réponses prêtes pour l'audit en secondes",
        desc: "Chaque réponse remonte à la source. Quand l'auditeur demande, vous cliquez sur la citation — le document original s'ouvre avec la phrase pertinente surlignée.",
      },
      {
        title: "Références croisées entre types de documents",
        desc: "Contrats, avenants, bons de commande, factures, avoirs — Evidoc les connecte tous. Une question couvre tout.",
      },
      {
        title: "Détecte ce que les humains manquent",
        desc: "\"Acme\" sur la facture et \"ACME Corporation\" dans le contrat ? Même entité, liée automatiquement. Changement de tarif dans l'avenant #3 ? Trouvé et cité.",
      },
    ],
    exampleQueries: [
      { question: "Ces factures correspondent-elles aux termes du contrat ?", context: "Chaque tarif, quantité et condition comparés — écarts cités des deux documents." },
      { question: "Quel est le taux horaire convenu pour les réparations d'urgence ?", context: "Trouve la clause exacte, même si le tarif a changé dans un avenant." },
      { question: "Quelles factures dépassent le budget approuvé ?", context: "Croise les montants des bons de commande avec les totaux des factures, sources citées." },
      { question: "Quelles sont les conditions de paiement pour tous les contrats fournisseurs ?", context: "Net 30, Net 60, remises pour paiement anticipé — tout extrait et cité." },
      { question: "Des fournisseurs ont-ils modifié leurs tarifs au cours des 12 derniers mois ?", context: "Compare les accords initiaux aux avenants et dernières factures." },
    ],
    ctaText: "Essayez Evidoc Gratuitement pour la Finance",
  },

  compliance: {
    slug: "compliance",
    badge: "Conformité et Audit",
    heroTitle: "Quand l'auditeur demande,<br>répondez en secondes.",
    heroSubtitle: "Trouvez exactement où vos politiques répondent à chaque exigence — cité jusqu'à la phrase, surligné sur la page originale.",
    painPoints: [
      {
        title: "La préparation d'audit prend des jours",
        desc: "\"Où vos politiques traitent-elles de la rétention des données ?\" L'équipe conformité passe 3 jours à chercher dans plus de 40 documents pour construire la réponse.",
      },
      {
        title: "Les politiques sont dispersées",
        desc: "La politique de données dit une chose, le règlement intérieur dit autre chose, et la documentation SOC 2 référence une troisième version. Laquelle est à jour ?",
      },
      {
        title: "L'analyse des écarts est manuelle",
        desc: "Comparer vos politiques à une nouvelle réglementation signifie lire chaque document et cartographier les exigences manuellement. Pour une équipe de 3 personnes, cela prend des semaines.",
      },
      {
        title: "Prouver la conformité nécessite des preuves",
        desc: "L'auditeur ne veut pas un résumé. Il veut le texte exact de la politique, la version exacte, dans le document exact. Les captures d'écran et surlignages manuels ne sont pas scalables.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Répondez aux questions d'audit instantanément",
        desc: "\"Où nos politiques traitent-elles de la rétention des données ?\" — Evidoc trouve chaque disposition pertinente dans tous les documents, citée jusqu'à la phrase exacte.",
      },
      {
        title: "Preuves cliquables pour les auditeurs",
        desc: "Partagez la réponse avec les citations. L'auditeur clique — il voit la phrase exacte surlignée sur le document de politique original. Sans allers-retours.",
      },
      {
        title: "Analyse des écarts de politiques en minutes",
        desc: "Téléchargez la nouvelle réglementation et vos politiques existantes. Demandez \"Quelles exigences ne sont pas couvertes ?\" — écarts cités des deux côtés.",
      },
      {
        title: "Suivez la cohérence des politiques",
        desc: "\"Le règlement intérieur est-il aligné avec notre politique de données sur les durées de conservation ?\" Evidoc trouve les incohérences et cite les deux versions.",
      },
    ],
    exampleQueries: [
      { question: "Où nos politiques traitent-elles de la rétention des données ?", context: "Chaque clause de conservation dans tous les documents de politiques, avec citations exactes." },
      { question: "Quelles procédures doivent être mises à jour pour la nouvelle norme ISO ?", context: "Analyse des écarts entre les procédures actuelles et la nouvelle norme, avec les deux côtés cités." },
      { question: "Quel est notre délai de notification en cas de violation de données ?", context: "Trouve les exigences de notification dans la politique de confidentialité, le plan de réponse aux incidents et les contrats." },
      { question: "Nos accords fournisseurs incluent-ils des clauses de traitement des données ?", context: "Examine tous les contrats fournisseurs pour le langage DPA, citant les clauses présentes et manquantes." },
      { question: "Quelles formations des employés sont requises par nos politiques ?", context: "Extrait toutes les exigences de formation du règlement intérieur, de la politique de sécurité et des docs de conformité." },
    ],
    testimonial: {
      quote: "Notre dernière préparation d'audit SOC 2 est passée de 2 semaines à 2 jours. Chaque question d'auditeur répondue avec le texte exact de la politique, cité et cliquable.",
      author: "Utilisateur en Accès Anticipé, Responsable Conformité",
    },
    ctaText: "Essayez Evidoc Gratuitement pour la Conformité",
  },

  research: {
    slug: "research",
    badge: "Recherche et Université",
    heroTitle: "Lisez 50 articles.<br>Ou posez-leur une question.",
    heroSubtitle: "Synthétisez les résultats d'articles de recherche, d'études cliniques et de rapports techniques — chaque affirmation tracée jusqu'à la source.",
    painPoints: [
      {
        title: "Les revues de littérature prennent des semaines",
        desc: "Lire 50 articles pour comprendre l'état de la recherche. Surligner, prendre des notes, croiser les références — c'est rigoureux mais terriblement lent.",
      },
      {
        title: "Les résultats sont enfouis dans le contexte",
        desc: "Le résultat clé est à la page 14 de l'article #37, mais il contredit un résultat à la page 8 de l'article #12. Vous ne le découvrez qu'après avoir lu les deux entièrement.",
      },
      {
        title: "Le suivi des citations est manuel",
        desc: "Vous vous souvenez d'avoir lu quelque chose de pertinent mais ne savez plus dans quel article. Vous relisez alors 20 articles pour retrouver une phrase.",
      },
      {
        title: "Les résumés IA perdent les nuances",
        desc: "ChatGPT résume un article mais omet les réserves. \"Efficace dans 80 % des cas\" devient \"efficace\" — et vous ne pouvez pas vérifier sans relire.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Interrogez l'ensemble de votre corpus",
        desc: "Téléchargez 50 articles. Demandez \"Que disent ces études sur le traitement X ?\" — résultats consolidés de chaque article, cités jusqu'à la phrase exacte.",
      },
      {
        title: "Chaque affirmation est traçable",
        desc: "\"Article 12, page 8, paragraphe 3\" — cliquez sur la citation et voyez la phrase exacte surlignée. Aucune ambiguïté sur ce que l'article original disait réellement.",
      },
      {
        title: "Trouvez les contradictions automatiquement",
        desc: "\"Ces articles sont-ils en désaccord sur l'efficacité de la méthode Y ?\" — Evidoc trouve les résultats contradictoires et cite les deux côtés.",
      },
      {
        title: "Fonctionne avec tous types de documents",
        desc: "PDF, documents Word, tableurs avec données, articles historiques numérisés — tous connectés, tous interrogeables, tous cités.",
      },
    ],
    exampleQueries: [
      { question: "Que disent ces articles sur l'efficacité du traitement X ?", context: "Résultats consolidés de 50 articles avec citations individuelles pour chaque affirmation." },
      { question: "Quelles études rapportent des effets indésirables ?", context: "Chaque mention d'effets indésirables ou secondaires — cité par article." },
      { question: "Comment les tailles d'échantillon se comparent-elles entre ces études ?", context: "Extrait les détails méthodologiques de chaque article avec les sources citées." },
      { question: "Des articles contredisent-ils les résultats de Smith et al. 2024 ?", context: "Trouve les conclusions contradictoires et cite les passages spécifiques de chaque article." },
      { question: "Quelles lacunes de recherche sont identifiées dans cette littérature ?", context: "Compile les sections de travaux futurs et de limitations de tous les articles." },
    ],
    ctaText: "Essayez Evidoc Gratuitement pour la Recherche",
  },

  realestate: {
    slug: "real-estate",
    badge: "Immobilier et Propriété",
    heroTitle: "Chaque clause. Chaque contre-offre.<br>Croisées et vérifiées.",
    heroSubtitle: "Comparez les offres, examinez les baux et détectez les incohérences dans les documents immobiliers — avec une preuve à chaque réponse.",
    painPoints: [
      {
        title: "Les comparaisons d'offres sont fastidieuses",
        desc: "Trois contre-offres de 30 pages chacune. Qu'est-ce qui a changé ? Les agents les comparent manuellement, paragraphe par paragraphe, en espérant ne rien rater.",
      },
      {
        title: "Les portefeuilles de baux sont ingérables",
        desc: "Une société de gestion immobilière avec 200 baux ne peut pas répondre rapidement à \"Quels baux autorisent la sous-location ?\" sans tous les lire.",
      },
      {
        title: "Les rapports d'inspection s'accumulent",
        desc: "Inspections annuelles, dossiers de maintenance, rapports d'entrepreneurs — ils sont classés mais jamais croisés. Les problèmes récurrents passent inaperçus.",
      },
      {
        title: "La due diligence est une course contre la montre",
        desc: "Acquisition d'un bien ? Rapports environnementaux, documents de titre, registres de zonage — tout doit être examiné dans un délai serré.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Comparez les documents instantanément",
        desc: "Téléchargez l'offre initiale et la contre-offre. Demandez \"Qu'est-ce qui a changé ?\" — chaque différence citée des deux versions.",
      },
      {
        title: "Recherchez dans tout votre portefeuille de baux",
        desc: "\"Quels baux ont une politique animaux ?\" \"Quelle est la clause moyenne d'indexation de loyer ?\" Une question sur 200 baux, chaque réponse citée.",
      },
      {
        title: "Connectez l'historique de maintenance",
        desc: "Téléchargez les rapports d'inspection, factures d'entrepreneurs et contrats de service. Demandez \"Le système CVC a-t-il été entretenu conformément au contrat ?\"",
      },
      {
        title: "Accélérez la due diligence",
        desc: "Téléchargez le dossier complet. Posez vos questions au fur et à mesure — chaque réponse remonte au document source. Due diligence en jours, pas en semaines.",
      },
    ],
    exampleQueries: [
      { question: "Qu'est-ce qui a changé dans la contre-offre ?", context: "Chaque terme révisé, clause ajoutée et condition supprimée — cités des deux versions." },
      { question: "Quels baux expirent dans les 6 prochains mois ?", context: "Dates d'expiration extraites de tous les baux avec conditions de renouvellement citées." },
      { question: "Les rapports d'inspection signalent-ils des problèmes récurrents ?", context: "Tendances sur plusieurs années de rapports, chaque occurrence citée." },
      { question: "Quels sont les charges de copropriété sur tous les baux commerciaux ?", context: "Conditions de charges communes comparées dans tout le portefeuille." },
      { question: "Y a-t-il des préoccupations environnementales dans le dossier de due diligence ?", context: "Résultats des rapports environnementaux, études et évaluations — tous cités." },
    ],
    ctaText: "Essayez Evidoc Gratuitement pour l'Immobilier",
  },

  personal: {
    slug: "personal",
    badge: "Personnel et Quotidien",
    heroTitle: "Vos documents,<br>enfin lisibles.",
    heroSubtitle: "Polices d'assurance, documents fiscaux, dossiers médicaux — posez une question en langage courant, obtenez une réponse fiable.",
    painPoints: [
      {
        title: "Les polices d'assurance sont illisibles",
        desc: "80 pages de jargon juridique. Vous devez savoir si votre toit est couvert, mais la réponse est enfouie dans les exclusions, sous-limites et termes définis renvoyant à d'autres sections.",
      },
      {
        title: "Les documents fiscaux sont déroutants",
        desc: "W-2, 1099, reçus de déductions — vous savez que l'information est là, mais trouver le chiffre précis prend plus de temps que nécessaire.",
      },
      {
        title: "Les dossiers médicaux sont éparpillés",
        desc: "Résultats de laboratoire d'un prestataire, notes du spécialiste d'un autre, rapports d'imagerie d'un troisième. Avoir une vue d'ensemble implique de tout lire.",
      },
      {
        title: "Les accords juridiques sont intimidants",
        desc: "Contrats de location, contrats de travail, documents de prêt — vous les avez signés mais n'êtes pas tout à fait sûr de ce que vous avez accepté.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Posez votre question en langage courant",
        desc: "\"Mon assurance couvre-t-elle les dégâts des eaux ?\" — Evidoc trouve la couverture, les exclusions et les limites, cités jusqu'au texte exact de la police.",
      },
      {
        title: "Vérifiez chaque réponse",
        desc: "Ne prenez pas l'IA au mot. Cliquez sur la citation — voyez la phrase exacte surlignée sur le document original. C'est vous qui jugez.",
      },
      {
        title: "Téléchargez n'importe quoi",
        desc: "PDF, documents numérisés, photos de papiers — Evidoc les lit tous. Plus de 15 formats pris en charge.",
      },
      {
        title: "13 langues prises en charge",
        desc: "Posez votre question dans votre langue. Evidoc détecte automatiquement et répond en conséquence — avec la saisie vocale pour une utilisation mains libres.",
      },
    ],
    exampleQueries: [
      { question: "Que couvre réellement mon assurance ?", context: "Couverture, exclusions, franchises et limites — tout cité de votre police." },
      { question: "Quelle est ma franchise pour les urgences ?", context: "Trouve le montant exact avec la clause spécifique de la police." },
      { question: "Mon propriétaire peut-il augmenter le loyer avant la fin du bail ?", context: "Clauses d'ajustement de loyer citées de votre contrat de location." },
      { question: "Quelles sont les pénalités pour remboursement anticipé de prêt ?", context: "Conditions de remboursement anticipé de votre contrat de prêt, citées à la section exacte." },
      { question: "Qu'a recommandé mon médecin lors de la dernière visite ?", context: "Extrait les recommandations des notes de consultation avec citations exactes." },
    ],
    ctaText: "Essayez Evidoc Gratuitement",
  },
};
