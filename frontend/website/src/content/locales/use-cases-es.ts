import type { UseCase } from "../use-cases";

export const useCasesEs: Record<string, UseCase> = {
  legal: {
    slug: "legal",
    badge: "Legal",
    heroTitle: "Deja de leer contratos.<br>Empieza a preguntarles.",
    heroSubtitle: "Revisa carteras completas de contratos en minutos. Cada cláusula citada hasta la oración exacta — haz clic para verificar en la página original.",
    painPoints: [
      {
        title: "La revisión de contratos toma semanas",
        desc: "Los paralegales leen manualmente cientos de contratos buscando cláusulas específicas. Una sola revisión de cartera puede llevar de 6 a 12 semanas.",
      },
      {
        title: "Ctrl+F no encuentra lo importante",
        desc: "\"Cambio de control\" puede estar escrito como \"transferencia de propiedad\", \"cesión de derechos\" o enterrado en una sección de definiciones. La búsqueda por palabras clave no encuentra lo que no puede predecir.",
      },
      {
        title: "Resúmenes de IA que no puedes citar",
        desc: "ChatGPT resumirá tu contrato — pero cuando el abogado contrario pregunte \"¿dónde dice eso?\", volverás a la búsqueda manual.",
      },
      {
        title: "Las referencias cruzadas son propensas a errores",
        desc: "El contrato principal dice una cosa, la enmienda dice otra, y la carta complementaria contradice ambos. Encontrar estas inconsistencias manualmente es donde ocurren los errores.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Pregunta en toda tu cartera",
        desc: "Sube 500 contratos. Haz una pregunta. Evidoc encuentra cada cláusula relevante en cada documento — citada hasta la oración exacta.",
      },
      {
        title: "Haz clic en cualquier cita para verificar",
        desc: "Cada respuesta incluye citas numeradas. Haz clic en una — el PDF original se abre con la oración exacta resaltada. Verificación en segundos, no en horas.",
      },
      {
        title: "Detecta inconsistencias automáticamente",
        desc: "\"¿Los términos de la enmienda coinciden con el contrato principal?\" Evidoc cruza referencias de ambos documentos y cita cada discrepancia.",
      },
      {
        title: "Entiende el lenguaje jurídico",
        desc: "\"Acme Corp\", \"Acme Corporation\" y \"el Vendedor\" — Evidoc los vincula automáticamente. Lee como un abogado, no como un motor de búsqueda.",
      },
    ],
    exampleQueries: [
      { question: "¿Qué contratos tienen una cláusula de cambio de control?", context: "En una cartera de 200 contratos — cada cláusula relevante citada en segundos." },
      { question: "¿Cuáles son las disposiciones de terminación en el contrato de Acme?", context: "Cada cláusula relacionada con terminación, incluyendo enmiendas y cartas complementarias." },
      { question: "¿Difieren los términos de indemnización entre los contratos de EE.UU. y la UE?", context: "Comparación entre documentos con diferencias citadas de ambas versiones." },
      { question: "¿Qué contratos vencen en los próximos 90 días?", context: "Extracción de fechas en todos los documentos con enlaces a la cláusula exacta." },
      { question: "¿Hay obligaciones de no competencia que sobrevivan a la terminación?", context: "Encuentra cláusulas de supervivencia incluso cuando están redactadas de forma diferente entre acuerdos." },
    ],
    testimonial: {
      quote: "Antes tardábamos 3 días en cruzar referencias de contratos. Ahora hacemos una pregunta y obtenemos cada cláusula relevante — citada hasta la oración exacta.",
      author: "Usuario de Acceso Anticipado, Operaciones Legales",
    },
    ctaText: "Prueba Evidoc Gratis para Legal",
  },

  finance: {
    slug: "finance",
    badge: "Finanzas y Compras",
    heroTitle: "Cada factura verificada.<br>Cada discrepancia citada.",
    heroSubtitle: "Compara facturas con contratos, detecta sobrecargos y prepara respuestas de auditoría — con pruebas en las que puedes hacer clic.",
    painPoints: [
      {
        title: "La verificación de facturas es manual",
        desc: "Los equipos de compras comparan facturas con contratos línea por línea. Con más de 500 facturas al mes, los sobrecargos se escapan — costando un promedio de $230.000 anuales.",
      },
      {
        title: "Los auditores quieren pruebas, no resúmenes",
        desc: "Cuando el auditor pregunta \"¿dónde dice que la tarifa es $150/hora?\", necesitas la cláusula exacta — no un resumen de ChatGPT.",
      },
      {
        title: "Los registros financieros abarcan docenas de documentos",
        desc: "El contrato, las enmiendas, las órdenes de compra, las facturas, las notas de crédito — la respuesta está dispersa en 20 documentos en 3 formatos diferentes.",
      },
      {
        title: "El cierre de mes tarda demasiado",
        desc: "Conciliar registros financieros, verificar cargos y preparar documentación para revisión — es preciso pero dolorosamente lento.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Compara facturas con contratos al instante",
        desc: "\"¿Estas facturas coinciden con las tarifas acordadas?\" Sube ambos — Evidoc cita cada discrepancia con la tarifa exacta de cada documento.",
      },
      {
        title: "Respuestas listas para auditoría en segundos",
        desc: "Cada respuesta se remonta a la fuente. Cuando el auditor pregunta, haces clic en la cita — el documento original se abre con la oración relevante resaltada.",
      },
      {
        title: "Referencias cruzadas entre tipos de documentos",
        desc: "Contratos, enmiendas, órdenes de compra, facturas, notas de crédito — Evidoc los conecta todos. Una pregunta abarca todo.",
      },
      {
        title: "Detecta lo que los humanos pasan por alto",
        desc: "\"Acme\" en la factura y \"ACME Corporation\" en el contrato? Misma entidad, vinculada automáticamente. ¿Cambios de tarifa en la enmienda #3? Encontrados y citados.",
      },
    ],
    exampleQueries: [
      { question: "¿Estas facturas coinciden con los términos del contrato?", context: "Cada tarifa, cantidad y término comparados — discrepancias citadas de ambos documentos." },
      { question: "¿Cuál es la tarifa por hora acordada para reparaciones de emergencia?", context: "Encuentra la cláusula exacta, incluso si la tarifa cambió en una enmienda." },
      { question: "¿Qué facturas exceden el presupuesto aprobado?", context: "Cruza referencias de montos de órdenes de compra contra totales de facturas con fuentes citadas." },
      { question: "¿Cuáles son los términos de pago en todos los contratos de proveedores?", context: "Net 30, Net 60, descuentos por pronto pago — todos extraídos y citados." },
      { question: "¿Algún proveedor ha cambiado sus tarifas en los últimos 12 meses?", context: "Compara acuerdos originales contra enmiendas y últimas facturas." },
    ],
    ctaText: "Prueba Evidoc Gratis para Finanzas",
  },

  compliance: {
    slug: "compliance",
    badge: "Cumplimiento y Auditoría",
    heroTitle: "Cuando el auditor pregunte,<br>responde en segundos.",
    heroSubtitle: "Encuentra exactamente dónde tus políticas abordan cualquier requisito — citado hasta la oración, resaltado en la página original.",
    painPoints: [
      {
        title: "La preparación de auditorías toma días",
        desc: "\"¿Dónde abordan tus políticas la retención de datos?\" El equipo de cumplimiento pasa 3 días buscando en más de 40 documentos de políticas para construir la respuesta.",
      },
      {
        title: "Las políticas están dispersas",
        desc: "La política de datos dice una cosa, el manual del empleado dice otra, y la documentación SOC 2 referencia una tercera versión. ¿Cuál es la vigente?",
      },
      {
        title: "El análisis de brechas es manual",
        desc: "Comparar tus políticas con una nueva regulación o estándar significa leer cada documento de política y mapear requisitos manualmente. Para un equipo de 3 personas, son semanas.",
      },
      {
        title: "Demostrar cumplimiento necesita evidencia",
        desc: "El auditor no quiere un resumen. Quiere el lenguaje exacto de la política, la versión exacta, en el documento exacto. Capturas de pantalla y resaltados manuales no son escalables.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Responde preguntas de auditoría al instante",
        desc: "\"¿Dónde abordan nuestras políticas la retención de datos?\" — Evidoc encuentra cada declaración de política relevante en todos los documentos, citada hasta la oración exacta.",
      },
      {
        title: "Evidencia clicable para auditores",
        desc: "Comparte la respuesta con citas. El auditor hace clic — ve la oración exacta resaltada en el documento de política original. Sin ida y vuelta.",
      },
      {
        title: "Análisis de brechas de políticas en minutos",
        desc: "Sube la nueva regulación y tus políticas existentes. Pregunta \"¿Qué requisitos no están cubiertos en nuestras políticas actuales?\" — brechas citadas de ambos lados.",
      },
      {
        title: "Rastrea la consistencia de políticas",
        desc: "\"¿El manual del empleado se alinea con nuestra política de datos sobre períodos de retención?\" Evidoc encuentra inconsistencias entre documentos y cita ambas versiones.",
      },
    ],
    exampleQueries: [
      { question: "¿Dónde abordan nuestras políticas la retención de datos?", context: "Cada cláusula de retención en todos los documentos de políticas, con citas exactas." },
      { question: "¿Qué POEs necesitan actualizarse para el nuevo estándar ISO?", context: "Análisis de brechas entre POEs actuales y el nuevo estándar, con ambos lados citados." },
      { question: "¿Cuál es nuestro plazo de notificación de violación de datos?", context: "Encuentra los requisitos de notificación en la política de privacidad, plan de respuesta a incidentes y contratos." },
      { question: "¿Nuestros acuerdos con proveedores incluyen cláusulas de procesamiento de datos?", context: "Revisa todos los contratos de proveedores buscando lenguaje de DPA, citando cláusulas presentes y faltantes." },
      { question: "¿Qué capacitación de empleados requieren nuestras políticas?", context: "Extrae todos los requisitos de capacitación del manual, política de seguridad y documentos de cumplimiento." },
    ],
    testimonial: {
      quote: "Nuestra última preparación de auditoría SOC 2 pasó de 2 semanas a 2 días. Cada pregunta del auditor respondida con el lenguaje exacto de la política, citado y clicable.",
      author: "Usuario de Acceso Anticipado, Gerente de Cumplimiento",
    },
    ctaText: "Prueba Evidoc Gratis para Cumplimiento",
  },

  research: {
    slug: "research",
    badge: "Investigación y Academia",
    heroTitle: "Lee 50 artículos.<br>O hazles una pregunta.",
    heroSubtitle: "Sintetiza hallazgos de artículos de investigación, estudios clínicos e informes técnicos — cada afirmación rastreada hasta la fuente.",
    painPoints: [
      {
        title: "Las revisiones bibliográficas toman semanas",
        desc: "Leer 50 artículos para entender el estado de la investigación sobre un tema. Subrayar, tomar notas, cruzar referencias — es exhaustivo pero dolorosamente lento.",
      },
      {
        title: "Los hallazgos están enterrados en contexto",
        desc: "El resultado clave está en la página 14 del artículo #37, pero contradice un hallazgo en la página 8 del artículo #12. Solo lo descubres después de leer ambos completos.",
      },
      {
        title: "El rastreo de citas es manual",
        desc: "Recuerdas haber leído algo relevante pero no recuerdas en qué artículo. Ahora estás releyendo 20 artículos para encontrar una oración.",
      },
      {
        title: "Los resúmenes de IA pierden los matices",
        desc: "ChatGPT resume un artículo pero omite las advertencias. \"Efectivo en el 80% de los casos\" se convierte en \"efectivo\" — y no puedes verificar sin releer.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Pregunta en todo tu corpus",
        desc: "Sube 50 artículos. Pregunta \"¿Qué dicen estos estudios sobre el tratamiento X?\" — hallazgos consolidados de cada artículo, citados hasta la oración exacta.",
      },
      {
        title: "Cada afirmación es rastreable",
        desc: "\"Artículo 12, página 8, párrafo 3\" — haz clic en la cita y ve la oración exacta resaltada. Sin ambigüedad sobre lo que realmente dice el artículo original.",
      },
      {
        title: "Encuentra contradicciones automáticamente",
        desc: "\"¿Alguno de estos artículos discrepa sobre la efectividad del método Y?\" — Evidoc encuentra hallazgos contradictorios y cita ambos lados.",
      },
      {
        title: "Funciona con distintos tipos de documentos",
        desc: "PDFs, documentos de Word, hojas de cálculo con tablas de datos, artículos históricos escaneados — todos conectados, todos buscables, todos citados.",
      },
    ],
    exampleQueries: [
      { question: "¿Qué dicen estos artículos sobre la eficacia del tratamiento X?", context: "Hallazgos consolidados de 50 artículos con citas individuales para cada afirmación." },
      { question: "¿Qué estudios reportan efectos adversos?", context: "Cada mención de efectos adversos, efectos secundarios o resultados negativos — citados por artículo." },
      { question: "¿Cómo se comparan los tamaños de muestra entre estos estudios?", context: "Extrae detalles de metodología de cada artículo con fuentes citadas." },
      { question: "¿Algún artículo contradice los hallazgos de Smith et al. 2024?", context: "Encuentra conclusiones contradictorias y cita los pasajes específicos de cada artículo." },
      { question: "¿Qué vacíos de investigación se identifican en esta literatura?", context: "Compila secciones de trabajo futuro y limitaciones de todos los artículos." },
    ],
    ctaText: "Prueba Evidoc Gratis para Investigación",
  },

  realestate: {
    slug: "real-estate",
    badge: "Inmobiliaria y Propiedad",
    heroTitle: "Cada cláusula. Cada contraoferta.<br>Con referencias cruzadas.",
    heroSubtitle: "Compara ofertas, revisa arrendamientos y detecta discrepancias en documentos inmobiliarios — con prueba en cada respuesta.",
    painPoints: [
      {
        title: "Las comparaciones de ofertas son tediosas",
        desc: "Tres contraofertas, cada una de 30 páginas. ¿Qué cambió? Los agentes las comparan manualmente, párrafo por párrafo, esperando no pasar por alto un término revisado.",
      },
      {
        title: "Las carteras de arrendamiento son inmanejables",
        desc: "Una empresa de gestión inmobiliaria con 200 arrendamientos no puede responder rápidamente \"¿Cuáles permiten subarrendamiento?\" sin leer cada uno.",
      },
      {
        title: "Los informes de inspección se acumulan",
        desc: "Inspecciones anuales, registros de mantenimiento, informes de contratistas — se archivan pero nunca se cruzan referencias. Los patrones pasan desapercibidos hasta que se convierten en problemas.",
      },
      {
        title: "La diligencia debida es una carrera contra el tiempo",
        desc: "¿Adquiriendo una propiedad? Informes ambientales, documentos de título, registros de zonificación, resúmenes de arrendamiento — todo necesita revisión bajo un plazo ajustado.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Compara documentos al instante",
        desc: "Sube la oferta original y la contraoferta. Pregunta \"¿Qué cambió?\" — cada diferencia citada de ambas versiones.",
      },
      {
        title: "Busca en toda tu cartera de arrendamientos",
        desc: "\"¿Qué arrendamientos tienen política de mascotas?\" \"¿Cuál es la cláusula promedio de escalamiento de renta?\" Una pregunta en 200 arrendamientos, cada respuesta citada.",
      },
      {
        title: "Conecta el historial de mantenimiento",
        desc: "Sube informes de inspección, facturas de contratistas y acuerdos de servicio. Pregunta \"¿Se ha dado servicio al sistema HVAC según los términos del contrato?\"",
      },
      {
        title: "Acelera la diligencia debida",
        desc: "Sube todo el paquete de documentos. Haz preguntas sobre la marcha — cada respuesta se remonta al documento fuente. Diligencia debida en días, no semanas.",
      },
    ],
    exampleQueries: [
      { question: "¿Qué cambió en la contraoferta?", context: "Cada término revisado, cláusula añadida y condición eliminada — citados de ambas versiones." },
      { question: "¿Qué arrendamientos vencen en los próximos 6 meses?", context: "Fechas de vencimiento extraídas de todos los arrendamientos con términos de renovación citados." },
      { question: "¿Los informes de inspección señalan problemas recurrentes?", context: "Patrones a través de años de informes, cada ocurrencia citada." },
      { question: "¿Cuáles son los cargos CAM en todos los arrendamientos comerciales?", context: "Términos de Mantenimiento de Áreas Comunes comparados en toda la cartera." },
      { question: "¿Hay preocupaciones ambientales en el paquete de diligencia debida?", context: "Hallazgos de informes ambientales, estudios y evaluaciones — todos citados." },
    ],
    ctaText: "Prueba Evidoc Gratis para Inmobiliaria",
  },

  personal: {
    slug: "personal",
    badge: "Personal y Cotidiano",
    heroTitle: "Tus documentos,<br>por fin legibles.",
    heroSubtitle: "Pólizas de seguro, documentos fiscales, historiales médicos — haz una pregunta en lenguaje sencillo, obtén una respuesta en la que puedas confiar.",
    painPoints: [
      {
        title: "Las pólizas de seguro son ilegibles",
        desc: "80 páginas de jerga legal. Necesitas saber si tu techo está cubierto, pero la respuesta está enterrada en exclusiones, sublímites y términos definidos que referencian otras secciones.",
      },
      {
        title: "Los documentos fiscales son confusos",
        desc: "W-2, 1099, recibos de deducciones — sabes que la información está ahí, pero encontrar el número específico que necesitas toma más tiempo del que debería.",
      },
      {
        title: "Los historiales médicos están dispersos",
        desc: "Resultados de laboratorio de un proveedor, notas del especialista de otro, informes de imagen de un tercero. Obtener un panorama completo implica leer todo.",
      },
      {
        title: "Los acuerdos legales son intimidantes",
        desc: "Contratos de alquiler, contratos laborales, documentos de préstamo — los firmaste pero no estás del todo seguro de lo que aceptaste.",
      },
    ],
    howEvidocHelps: [
      {
        title: "Pregunta en lenguaje sencillo",
        desc: "\"¿Mi seguro cubre daños por agua?\" — Evidoc encuentra la cobertura relevante, exclusiones y límites, citados hasta el lenguaje exacto de la póliza.",
      },
      {
        title: "Verifica cada respuesta",
        desc: "No confíes solo en la palabra de la IA. Haz clic en la cita — ve la oración exacta resaltada en el documento original. Tú decides si es correcto.",
      },
      {
        title: "Sube cualquier cosa",
        desc: "PDFs, documentos escaneados, fotos de papeles — Evidoc los lee todos. Más de 15 formatos compatibles.",
      },
      {
        title: "13 idiomas compatibles",
        desc: "Pregunta en tu idioma. Evidoc detecta automáticamente y responde de la misma forma — con entrada de voz para uso manos libres.",
      },
    ],
    exampleQueries: [
      { question: "¿Qué cubre realmente mi seguro?", context: "Cobertura, exclusiones, deducibles y límites — todo citado de tu póliza." },
      { question: "¿Cuál es mi deducible para visitas a urgencias?", context: "Encuentra el monto exacto con la cláusula específica de la póliza." },
      { question: "¿Puede mi arrendador subir el alquiler antes de que termine el contrato?", context: "Cláusulas de ajuste de renta citadas de tu contrato de arrendamiento." },
      { question: "¿Cuáles son las penalizaciones por pago anticipado del préstamo?", context: "Términos de prepago de tu contrato de préstamo, citados hasta la sección exacta." },
      { question: "¿Qué recomendó mi doctor en la última visita?", context: "Extrae recomendaciones de las notas de la visita con citas exactas." },
    ],
    ctaText: "Prueba Evidoc Gratis",
  },
};
