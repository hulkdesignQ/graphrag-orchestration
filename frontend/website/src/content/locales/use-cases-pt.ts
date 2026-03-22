import type { UseCase } from "../use-cases";

export const useCasesPt: Record<string, UseCase> = {
  legal: {
    slug: "legal",
    badge: "Jurídico",
    heroTitle: "Pare de ler contratos.<br>Comece a questioná-los.",
    heroSubtitle: "Revise portfólios inteiros de contratos em minutos. Cada cláusula citada até a frase exata — clique para verificar na página original.",
    painPoints: [
      {
        title: "A revisão de contratos leva semanas",
        desc: "Paralegais leem manualmente centenas de contratos procurando cláusulas específicas. Uma única revisão de portfólio pode levar de 6 a 12 semanas.",
      },
      {
        title: "Ctrl+F não encontra o que importa",
        desc: "\"Mudança de controle\" pode estar escrito como \"transferência de propriedade\", \"cessão de direitos\" ou enterrado numa seção de definições. A busca por palavras-chave não encontra o que não consegue prever.",
      },
      {
        title: "Resumos de IA que você não pode citar",
        desc: "O ChatGPT resume o seu contrato — mas quando o advogado da parte contrária pergunta \"onde está escrito?\", você volta à busca manual.",
      },
      {
        title: "Referências cruzadas são propensas a erros",
        desc: "O contrato principal diz uma coisa, a emenda diz outra, e a carta complementar contradiz ambos. Encontrar essas inconsistências manualmente é onde os erros acontecem.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Pergunte em todo o seu portfólio",
        desc: "Carregue 500 contratos. Faça uma pergunta. O Evidoc encontra cada cláusula relevante em cada documento — citada até a frase exata.",
      },
      {
        title: "Clique em qualquer citação para verificar",
        desc: "Cada resposta inclui citações numeradas. Clique numa — o PDF original abre com a frase exata destacada. Verificação em segundos, não horas.",
      },
      {
        title: "Detecta inconsistências automaticamente",
        desc: "\"Os termos da emenda correspondem ao contrato principal?\" O Evidoc faz referência cruzada de ambos os documentos e cita cada discrepância.",
      },
      {
        title: "Compreende a linguagem jurídica",
        desc: "\"Acme Corp\", \"Acme Corporation\" e \"o Vendedor\" — o Evidoc os vincula automaticamente. Lê como um advogado, não como um motor de busca.",
      },
    ],
    exampleQueries: [
      { question: "Quais contratos têm cláusula de mudança de controle?", context: "Num portfólio de 200 contratos — cada cláusula relevante citada em segundos." },
      { question: "Quais são as disposições de rescisão no contrato da Acme?", context: "Cada cláusula relacionada à rescisão, incluindo emendas e cartas complementares." },
      { question: "Os termos de indenização diferem entre os contratos dos EUA e da UE?", context: "Comparação entre documentos com diferenças citadas de ambas as versões." },
      { question: "Quais contratos vencem nos próximos 90 dias?", context: "Extração de datas de todos os documentos com links para a cláusula exata." },
      { question: "Existem obrigações de não competição que sobrevivem à rescisão?", context: "Encontra cláusulas de sobrevivência mesmo quando formuladas de forma diferente entre acordos." },
    ],
    testimonial: {
      quote: "Costumávamos gastar 3 dias em referências cruzadas de contratos. Agora fazemos uma pergunta e obtemos cada cláusula relevante — citada até a frase exata.",
      author: "Utilizador de Acesso Antecipado, Operações Jurídicas",
    },
    ctaText: "Experimente o Evidoc Grátis para Jurídico",
  },

  finance: {
    slug: "finance",
    badge: "Finanças e Compras",
    heroTitle: "Cada fatura verificada.<br>Cada discrepância citada.",
    heroSubtitle: "Compare faturas com contratos, detete sobrefaturações e prepare respostas de auditoria — com provas clicáveis.",
    painPoints: [
      {
        title: "A verificação de faturas é manual",
        desc: "As equipas de compras comparam faturas com contratos linha a linha. Com mais de 500 faturas por mês, sobrefaturações escapam — custando uma média de $230.000 anuais.",
      },
      {
        title: "Os auditores querem provas, não resumos",
        desc: "Quando o auditor pergunta \"onde está escrito que a taxa é $150/hora?\", precisa da cláusula exata — não de um resumo do ChatGPT.",
      },
      {
        title: "Os registos financeiros abrangem dezenas de documentos",
        desc: "O contrato, as emendas, as ordens de compra, as faturas, as notas de crédito — a resposta está espalhada por 20 documentos em 3 formatos diferentes.",
      },
      {
        title: "O fecho do mês demora demasiado",
        desc: "Reconciliar registos financeiros, verificar encargos e preparar documentação para revisão — é preciso mas dolorosamente lento.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Compare faturas e contratos instantaneamente",
        desc: "\"Estas faturas correspondem às taxas contratuais acordadas?\" Carregue ambos — o Evidoc cita cada discrepância com a taxa exata de cada documento.",
      },
      {
        title: "Respostas prontas para auditoria em segundos",
        desc: "Cada resposta é rastreável até à fonte. Quando o auditor pergunta, clique na citação — o documento original abre com a frase relevante destacada.",
      },
      {
        title: "Referências cruzadas entre tipos de documentos",
        desc: "Contratos, emendas, ordens de compra, faturas, notas de crédito — o Evidoc conecta todos. Uma pergunta abrange tudo.",
      },
      {
        title: "Deteta o que os humanos perdem",
        desc: "\"Acme\" na fatura e \"ACME Corporation\" no contrato? Mesma entidade, vinculada automaticamente. Alteração de taxa na emenda #3? Encontrada e citada.",
      },
    ],
    exampleQueries: [
      { question: "Estas faturas correspondem aos termos do contrato?", context: "Cada taxa, quantidade e condição comparadas — discrepâncias citadas de ambos os documentos." },
      { question: "Qual é a taxa horária acordada para reparações de emergência?", context: "Encontra a cláusula exata, mesmo que a taxa tenha mudado numa emenda." },
      { question: "Quais faturas excedem o orçamento aprovado?", context: "Cruza os valores das ordens de compra com os totais das faturas, com fontes citadas." },
      { question: "Quais são as condições de pagamento em todos os contratos de fornecedores?", context: "Net 30, Net 60, descontos por pagamento antecipado — tudo extraído e citado." },
      { question: "Algum fornecedor alterou as suas taxas nos últimos 12 meses?", context: "Compara acordos originais com emendas e faturas mais recentes." },
    ],
    ctaText: "Experimente o Evidoc Grátis para Finanças",
  },

  compliance: {
    slug: "compliance",
    badge: "Conformidade e Auditoria",
    heroTitle: "Quando o auditor perguntar,<br>responda em segundos.",
    heroSubtitle: "Encontre exatamente onde as suas políticas abordam cada requisito — citado até à frase, destacado na página original.",
    painPoints: [
      {
        title: "A preparação de auditoria leva dias",
        desc: "\"Onde as vossas políticas abordam a retenção de dados?\" A equipa de conformidade passa 3 dias a pesquisar mais de 40 documentos de políticas para construir a resposta.",
      },
      {
        title: "As políticas estão dispersas",
        desc: "A política de dados diz uma coisa, o manual do colaborador diz outra, e a documentação SOC 2 referencia uma terceira versão. Qual é a atual?",
      },
      {
        title: "A análise de lacunas é manual",
        desc: "Comparar as suas políticas com uma nova regulamentação significa ler cada documento de política e mapear requisitos manualmente. Para uma equipa de 3 pessoas, são semanas.",
      },
      {
        title: "Provar conformidade precisa de evidências",
        desc: "O auditor não quer um resumo. Quer a linguagem exata da política, a versão exata, no documento exato. Screenshots e destaques manuais não são escaláveis.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Responda a perguntas de auditoria instantaneamente",
        desc: "\"Onde as nossas políticas abordam a retenção de dados?\" — o Evidoc encontra cada declaração de política relevante em todos os documentos, citada até à frase exata.",
      },
      {
        title: "Evidências clicáveis para auditores",
        desc: "Partilhe a resposta com citações. O auditor clica — vê a frase exata destacada no documento de política original. Sem idas e voltas.",
      },
      {
        title: "Análise de lacunas de políticas em minutos",
        desc: "Carregue a nova regulamentação e as suas políticas existentes. Pergunte \"Quais requisitos não são cobertos pelas nossas políticas atuais?\" — lacunas citadas de ambos os lados.",
      },
      {
        title: "Acompanhe a consistência das políticas",
        desc: "\"O manual do colaborador está alinhado com a nossa política de dados sobre períodos de retenção?\" O Evidoc encontra inconsistências entre documentos e cita ambas as versões.",
      },
    ],
    exampleQueries: [
      { question: "Onde as nossas políticas abordam a retenção de dados?", context: "Cada cláusula de retenção em todos os documentos de políticas, com citações exatas." },
      { question: "Quais POPs precisam de atualização para o novo padrão ISO?", context: "Análise de lacunas entre POPs atuais e o novo padrão, ambos os lados citados." },
      { question: "Qual é o nosso prazo de notificação em caso de violação de dados?", context: "Encontra os requisitos de notificação na política de privacidade, plano de resposta a incidentes e contratos." },
      { question: "Os nossos acordos com fornecedores incluem cláusulas de processamento de dados?", context: "Revisa todos os contratos de fornecedores em busca de linguagem DPA, citando cláusulas presentes e ausentes." },
      { question: "Que formação de colaboradores é exigida pelas nossas políticas?", context: "Extrai todos os requisitos de formação do manual, política de segurança e documentos de conformidade." },
    ],
    testimonial: {
      quote: "A nossa última preparação de auditoria SOC 2 passou de 2 semanas para 2 dias. Cada pergunta do auditor respondida com a linguagem exata da política, citada e clicável.",
      author: "Utilizador de Acesso Antecipado, Gestor de Conformidade",
    },
    ctaText: "Experimente o Evidoc Grátis para Conformidade",
  },

  research: {
    slug: "research",
    badge: "Investigação e Academia",
    heroTitle: "Leia 50 artigos.<br>Ou faça-lhes uma pergunta.",
    heroSubtitle: "Sintetize descobertas de artigos de investigação, estudos clínicos e relatórios técnicos — cada afirmação rastreável até à fonte.",
    painPoints: [
      {
        title: "Revisões de literatura levam semanas",
        desc: "Ler 50 artigos para compreender o estado da investigação num tópico. Destacar, tomar notas, fazer referências cruzadas — minucioso mas dolorosamente lento.",
      },
      {
        title: "As descobertas estão enterradas no contexto",
        desc: "O resultado-chave está na página 14 do artigo #37, mas contradiz uma descoberta na página 8 do artigo #12. Só descobre isso depois de ler ambos completamente.",
      },
      {
        title: "O rastreio de citações é manual",
        desc: "Lembra-se de ter lido algo relevante mas não sabe em qual artigo. Agora está a reler 20 artigos para encontrar uma frase.",
      },
      {
        title: "Os resumos de IA perdem as nuances",
        desc: "O ChatGPT resume um artigo mas omite as ressalvas. \"Eficaz em 80% dos casos\" torna-se \"eficaz\" — e não pode verificar sem reler.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Pergunte em todo o seu corpus",
        desc: "Carregue 50 artigos. Pergunte \"O que dizem estes estudos sobre o tratamento X?\" — descobertas consolidadas de cada artigo, citadas até à frase exata.",
      },
      {
        title: "Cada afirmação é rastreável",
        desc: "\"Artigo 12, página 8, parágrafo 3\" — clique na citação e veja a frase exata destacada. Sem ambiguidade sobre o que o artigo original realmente disse.",
      },
      {
        title: "Encontra contradições automaticamente",
        desc: "\"Estes artigos discordam sobre a eficácia do método Y?\" — o Evidoc encontra descobertas contraditórias e cita ambos os lados.",
      },
      {
        title: "Funciona com todos os tipos de documentos",
        desc: "PDFs, documentos Word, folhas de cálculo com tabelas de dados, artigos históricos digitalizados — todos conectados, todos pesquisáveis, todos citados.",
      },
    ],
    exampleQueries: [
      { question: "O que dizem estes artigos sobre a eficácia do tratamento X?", context: "Descobertas consolidadas de 50 artigos com citações individuais para cada afirmação." },
      { question: "Quais estudos reportam efeitos adversos?", context: "Cada menção de efeitos adversos, efeitos secundários ou resultados negativos — citados por artigo." },
      { question: "Como se comparam os tamanhos de amostra entre estes estudos?", context: "Extrai detalhes metodológicos de cada artigo com fontes citadas." },
      { question: "Algum artigo contradiz as descobertas de Smith et al. 2024?", context: "Encontra conclusões contraditórias e cita as passagens específicas de cada artigo." },
      { question: "Quais lacunas de investigação são identificadas nesta literatura?", context: "Compila secções de trabalho futuro e limitações de todos os artigos." },
    ],
    ctaText: "Experimente o Evidoc Grátis para Investigação",
  },

  realestate: {
    slug: "real-estate",
    badge: "Imobiliário",
    heroTitle: "Cada cláusula. Cada contraproposta.<br>Com referência cruzada.",
    heroSubtitle: "Compare ofertas, revise arrendamentos e detete discrepâncias em documentos imobiliários — com prova em cada resposta.",
    painPoints: [
      {
        title: "As comparações de ofertas são tediosas",
        desc: "Três contrapropostas, cada uma com 30 páginas. O que mudou? Os agentes comparam-nas manualmente, parágrafo a parágrafo, esperando não perder um termo revisto.",
      },
      {
        title: "Os portfólios de arrendamento são incontroláveis",
        desc: "Uma empresa de gestão imobiliária com 200 arrendamentos não consegue responder rapidamente \"Quais permitem subarrendamento?\" sem ler cada um.",
      },
      {
        title: "Os relatórios de inspeção acumulam-se",
        desc: "Inspeções anuais, registos de manutenção, relatórios de empreiteiros — ficam arquivados mas nunca cruzados. Os padrões passam despercebidos até se tornarem problemas.",
      },
      {
        title: "A diligência devida é uma corrida contra o tempo",
        desc: "A adquirir um imóvel? Relatórios ambientais, documentos de propriedade, registos de zonamento — tudo precisa ser revisto num prazo apertado.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Compare documentos instantaneamente",
        desc: "Carregue a oferta original e a contraproposta. Pergunte \"O que mudou?\" — cada diferença citada de ambas as versões.",
      },
      {
        title: "Pesquise em todo o portfólio de arrendamento",
        desc: "\"Quais arrendamentos têm política de animais?\" \"Qual é a cláusula média de aumento de renda?\" Uma pergunta em 200 arrendamentos, cada resposta citada.",
      },
      {
        title: "Conecte o histórico de manutenção",
        desc: "Carregue relatórios de inspeção, faturas de empreiteiros e contratos de serviço. Pergunte \"O sistema AVAC foi mantido conforme os termos do contrato?\"",
      },
      {
        title: "Acelere a diligência devida",
        desc: "Carregue o pacote completo de documentos. Faça perguntas à medida que avança — cada resposta rastreável até ao documento fonte. Diligência devida em dias, não semanas.",
      },
    ],
    exampleQueries: [
      { question: "O que mudou na contraproposta?", context: "Cada termo revisto, cláusula adicionada e condição removida — citados de ambas as versões." },
      { question: "Quais arrendamentos expiram nos próximos 6 meses?", context: "Datas de expiração extraídas de todos os arrendamentos com termos de renovação citados." },
      { question: "Os relatórios de inspeção sinalizam problemas recorrentes?", context: "Padrões ao longo de anos de relatórios, cada ocorrência citada." },
      { question: "Quais são os encargos CAM em todos os arrendamentos comerciais?", context: "Termos de manutenção de áreas comuns comparados em todo o portfólio." },
      { question: "Há preocupações ambientais no pacote de diligência devida?", context: "Descobertas de relatórios ambientais, estudos e avaliações — todos citados." },
    ],
    ctaText: "Experimente o Evidoc Grátis para Imobiliário",
  },

  personal: {
    slug: "personal",
    badge: "Pessoal e Quotidiano",
    heroTitle: "Os seus documentos,<br>finalmente legíveis.",
    heroSubtitle: "Apólices de seguro, documentos fiscais, registos médicos — faça uma pergunta em linguagem simples, obtenha uma resposta de confiança.",
    painPoints: [
      {
        title: "As apólices de seguro são ilegíveis",
        desc: "80 páginas de jargão jurídico. Precisa saber se o seu telhado está coberto, mas a resposta está enterrada em exclusões, sublimites e termos definidos que referenciam outras secções.",
      },
      {
        title: "Os documentos fiscais são confusos",
        desc: "Declarações de rendimentos, recibos de deduções — sabe que a informação está lá, mas encontrar o número específico demora mais do que deveria.",
      },
      {
        title: "Os registos médicos estão dispersos",
        desc: "Resultados laboratoriais de um prestador, notas do especialista de outro, relatórios de imagem de um terceiro. Ter uma visão completa implica ler tudo.",
      },
      {
        title: "Os acordos legais são intimidantes",
        desc: "Contratos de arrendamento, contratos de trabalho, documentos de empréstimo — assinou-os mas não tem a certeza total do que concordou.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Pergunte em linguagem simples",
        desc: "\"O meu seguro cobre danos por água?\" — o Evidoc encontra a cobertura relevante, exclusões e limites, citados até à linguagem exata da apólice.",
      },
      {
        title: "Verifique cada resposta",
        desc: "Não confie apenas na palavra da IA. Clique na citação — veja a frase exata destacada no documento original. Decide se está correto.",
      },
      {
        title: "Carregue qualquer coisa",
        desc: "PDFs, documentos digitalizados, fotos de papéis — o Evidoc lê tudo. Mais de 15 formatos suportados.",
      },
      {
        title: "13 idiomas suportados",
        desc: "Pergunte no seu idioma. O Evidoc deteta automaticamente e responde da mesma forma — com entrada de voz para uso mãos-livres.",
      },
    ],
    exampleQueries: [
      { question: "O que o meu seguro realmente cobre?", context: "Cobertura, exclusões, franquias e limites — tudo citado da sua apólice." },
      { question: "Qual é a minha franquia para visitas às urgências?", context: "Encontra o valor exato com a cláusula específica da apólice." },
      { question: "O meu senhorio pode aumentar a renda antes do fim do contrato?", context: "Cláusulas de ajuste de renda citadas do seu contrato de arrendamento." },
      { question: "Quais são as penalizações por reembolso antecipado do empréstimo?", context: "Termos de pré-pagamento do seu contrato de empréstimo, citados até à secção exata." },
      { question: "O que o meu médico recomendou na última consulta?", context: "Extrai recomendações das notas da consulta com citações exatas." },
    ],
    ctaText: "Experimente o Evidoc Grátis",
  },
};
