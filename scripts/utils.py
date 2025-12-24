# Utility data and helpers for Auditel.
import json

_OBRA_PUBLICA_JSON = r'''[
  {
    "tipo": "Volumenes de obra pagados no ejecutados",
    "descripcion_irregularidad": "Por contrato: Es el resultado de la diferencia entre las cantidades estimadas y las obtenidas fisicamente. Por Administración Directa: Insumos: Es el resultado de la diferencia entre las cantidades facturadas y las obtenidas fisicamente. Mano de Obra: Es el resultado de la diferencia entre el número de jornales amparado en la listas de raya y los calculados con base a los trabajos fisicamente ejecutados.",
    "accion_promovida": "Probable Daño Patrimonial (PDP)",
    "acciones_irregularidad": [
      "Simulación de documentación técnica justificativa, toda vez, que los trabajos no han sido ejecutado o se encuentra en proceso constructivo.",
      "Se consideran en los números generadores medidas superiores a las físicamente ejecutadas.",
      "Adquisición de insumos superiores a los utilizados para la ejecución de los trabajos.",
      "Consideración de bajos rendimientos de las cuadrillas."
    ],
    "documentacion_soporte": [
      "Copia certificada de la cuenta pública del ente fiscalizado de los conceptos observados: Orden de pago, Pólizas contables, Transferencias, Presupuesto (catálogo de conceptos contratados), Contrato y convenio modificatorio, Facturas, estimaciones, números generadores, Bitácora de obra, Reporte fotográfico, Acta entrega recepción.",
      "Documentación integrada por el ente auditor: Levantamiento físico (croquis y/o planos), Cédula de cálculos realizados, Reporte fotográfico, Acta de auditoria donde consten los hechos observados."
    ],
    "normatividad_local_administracion_directa": "Artículos 10, 74, 75, 76, 77 de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_local_contrato": "Artículos 58, 59, 60 de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_federal_administracion_directa": "Artículos 70, 71, 72 y 73 de la Ley de Obras Públicas y Servicios Relacionados con la Mismas.",
    "normatividad_federal_contratacion": "Artículo 46 fracción XII, 53 y 55 de la Ley de Obras Públicas y Servicios Relacionados con la Mismas. Artículo 131 del Reglamento de la Ley de Obras Públicas y Servicios Relacionados con la Mismas."
  },
  {
    "tipo": "Conceptos de obra pagados no ejecutados",
    "descripcion_irregularidad": "Por contrato: Es el concepto de obra pagado no ejecutado a la fecha de la visita física. Por Administración Directa: Insumos y mano de obra: Es el insumo de obra facturado que no ha sido suministrado y ejecutado a la fecha de la visita física.",
    "accion_promovida": "Probable Daño Patrimonial (PDP)",
    "acciones_irregularidad": [
      "Se consideran en los números generadores conceptos no ejecutados a la fecha de la visita física.",
      "Falta de suministro de insumos para la ejecución de los trabajos a la fecha de la visita física.",
      "Trabajos no ejecutados a la fecha de la visita física."
    ],
    "documentacion_soporte": [
      "Copia certificada de la cuenta pública del ente fiscalizado de los conceptos observados: Orden de pago, Pólizas contables, Transferencias, Presupuesto (catálogo de conceptos contratados), Contrato y convenio modificatorio, Facturas, estimaciones, números generadores, Bitácora de obra, Reporte fotográfico, Acta entrega recepción.",
      "Documentación integrada por el ente auditor: Levantamiento físico (croquis y/o planos), Cédula de cálculos realizados, Reporte fotográfico, Acta de auditoria donde consten los hechos observados."
    ],
    "normatividad_local_administracion_directa": "Artículos 10, 74, 75, 76, 77 de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_local_contrato": "Artículos 58, 59, 60 de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_federal_administracion_directa": "Artículos 70, 71, 72 y 73 de la Ley de Obras Públicas y Servicios Relacionados con la Mismas.",
    "normatividad_federal_contratacion": "Artículo 46 fracción XII, 53 y 55 de la Ley de Obras Públicas y Servicios Relacionados con la Mismas. Artículo 131 del Reglamento de la Ley de Obras Públicas y Servicios Relacionados con la Mismas."
  },
  {
    "tipo": "Pago de obras sin acreditar su existencia física",
    "descripcion_irregularidad": "Por contrato / Administración Directa: Es la obra estimada no ejecutada o no ubicada en coordinación con personal adscrito al ente auditado a la fecha de la visita física.",
    "accion_promovida": "Pliego de Observaciones (PO) / Probable Daño Patrimonial (PDP)",
    "acciones_irregularidad": [
      "Simulación de documentación técnica justificativa, toda vez, que los trabajos no han sido ejecutado."
    ],
    "documentacion_soporte": [
      "Copia certificada de la cuenta pública del ente fiscalizado de la obra observada: Orden de pago, Pólizas contables, Transferencias, Presupuesto (catálogo de conceptos contratados), Contrato y convenio modificatorio, Facturas, estimaciones, números generadores, Bitácora de obra, Reporte fotográfico, Acta entrega recepción.",
      "Documentación integrada por el ente auditor: Levantamiento físico (croquis y/o planos), Cedula de cálculos realizados, Reporte fotográfico, Acta de auditoria donde consten los hechos observados."
    ],
    "normatividad_local_administracion_directa": "Artículos 10, 74, 75, 76, 77 de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_local_contrato": "Artículos 58, 59, 60 de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_federal_administracion_directa": "Artículos 70, 71, 72 y 73 de la Ley de Obras Públicas y Servicios Relacionados con la Mismas.",
    "normatividad_federal_contratacion": "Artículo 46 fracción XII, 53 y 55 de la Ley de Obras Públicas y Servicios Relacionados con la Mismas. Artículo 131 del Reglamento de la Ley de Obras Públicas y Servicios Relacionados con la Mismas."
  },
  {
    "tipo": "Procesos constructivos deficientes que causan afectaciones físicas en las obras",
    "descripcion_irregularidad": "Por contrato / Administración Directa: Son los procesos constructuivos deficientes en las obras públicas que dan como resultado defectos, fallas y deterioros, originados por la utilización de insumos de mala calidad y/o mano de obra no calificada.",
    "accion_promovida": "Probable Daño Patrimonial (PDP)",
    "acciones_irregularidad": [
      "Falta o deficiente supervición de los proceos constructivos.",
      "Utilización de insumos de mala calidad al no cumplir con las especificación tecnicas.",
      "Ejecución de los procesos constructivos, sin apego a lo establecido en los proyectos ejecutivos de la obra.",
      "Empleo de mano de obra no calificada."
    ],
    "documentacion_soporte": [
      "Copia certificada de la cuenta pública del ente fiscalizado de los conceptos observados: Orden de pago, Pólizas contables, Transferencias, Presupuesto (catálogo de conceptos contratados), Contrato y convenio modificatorio, Facturas, estimaciones, números generadores, Bitácora de obra, Reporte fotográfico, Acta entrega recepción, Fianza de vicios ocultos.",
      "Documentación integrada por el ente auditor: Levantamiento físico (croquis y/o planos), Cedula de cálculos realizados, Reporte fotográfico, Acta de auditoria donde consten los hechos observados."
    ],
    "normatividad_local_administracion_directa": "Artículos 10, 74, 75, 76, 77 de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_local_contrato": "Artículos 70, 71 de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_federal_administracion_directa": "Artículos 70, 71, 72 y 73 de la Ley de Obras Públicas y Servicios Relacionados con la Mismas.",
    "normatividad_federal_contratacion": "Artículo 66, 67 de la Ley de Obras Públicas y Servicios Relacionados con la Mismas."
  },
  {
    "tipo": "Pago de conceptos de obra, insumos, bienes o servicios a precios superiores al de mercado",
    "descripcion_irregularidad": "Por contrato: Es el resultado de la diferencia entre el precio unitario contratado y el analisis, cálculo e integración de los precios acorde con las condiciones de costos vigentes en la zona o region donde se ejecutaron los trabajos. Por Administración Directa: Es el resultado de la diferencia entre el precio facturado de insumos y/o pago de mano de obra respecto al analisis, cálculo e integración de los precios acorde con las condiciones de costos vigentes en la zona o region donde se ejecutaron los trabajos.",
    "accion_promovida": "Probable Daño Patrimonial (PDP)",
    "acciones_irregularidad": [
      "Costo de insumos por arriba de los costo de mercado.",
      "Bajos rendiemientos de mano de obra.",
      "Cantidad de insumos mayores a los necesarior por unidad de medida.",
      "Bajos rendiemientos de hora maquina.",
      "Porcentajes elevados de indirectos.",
      "Duplicidad de actividades entre conceptos de obra.",
      "Actividades incluidas en concepto no ejeutadas."
    ],
    "documentacion_soporte": [
      "Copia certificada de la cuenta pública del ente fiscalizado de los conceptos observados: Orden de pago, Pólizas contables, Tranferencias, Presupuesto (catálogo de conceptos contratados), Contrato y convenio modificatorio, Facturas, estimaciones, Reporte fotográfico, Tarjetas de Precios Unitarios.",
      "Documentación integrada por el ente auditor: Levantamiento físico (croquis y/o planos), Cedula de cálculos realizados, Reporte fotográfico, Acta de auditoria donde consten los hechos observados, Tarjeta de Precios Unitarios del OFS, Cotizaciones con racteristicas identicas, Tablas de rendimientos (maquinaria / cuadrillas)."
    ],
    "normatividad_local_administracion_directa": "Artículos 10, 74, 75, 76, 77 de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_local_contrato": "Artículos 1, 19 y 42 parrafo segúndo de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_federal_administracion_directa": "Artículos 70, 71, 72 y 73 de la Ley de Obras Públicas y Servicios Relacionados con la Mismas.",
    "normatividad_federal_contratacion": "Artículo 21 fracción XIII y 31 fracción XV, de la Ley de Obras Públicas y Servicios Relacionados con la Mismas. Artículo 21 fracción V, 65 fracción II, 186 del Reglamento de la Ley de Obras Públicas y Servicios Relacionados con la Mismas."
  },
  {
    "tipo": "Obras y/o conceptos pagados no fiscalizados por ocultamiento de documentación comprobatoria de su ejecución",
    "descripcion_irregularidad": "Por contrato / Administración Directa: Es la omisión de la integración de la documentación técnica justificativa de los trabajos pagados de la obra.",
    "accion_promovida": "Probable Daño Patrimonial (PDP)",
    "acciones_irregularidad": [
      "Falta de integración de la documentación tecnica justificativa.",
      "Financiamiento total de las obras ejecutadas.",
      "Simulación de proceos de adjudicación.",
      "Obras ejecutadas al final de la administración"
    ],
    "documentacion_soporte": [
      "Copia certificada de la cuenta pública del ente fiscalizado de los conceptos observados: Pólizas contables, Facturas (CFDI).",
      "Documentación integrada por el ente auditor: Acta de auditoria donde consten los hechos observados."
    ],
    "normatividad_local_administracion_directa": "Artículo 42 de la Ley General de Contabilidad Gubernamental.",
    "normatividad_local_contrato": "Artículo 42 de la Ley General de Contabilidad Gubernamental. Artículos 58, 59, 60, 78 de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios. Artículo 302 del Código Financiero para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_federal_administracion_directa": "Artículo 42 de la Ley General de Contabilidad Gubernamental. Artículos 70, 71, 72 y 73 de la Ley de Obras Públicas y Servicios Relacionados con la Mismas.",
    "normatividad_federal_contratacion": "Artículo 42 de la Ley General de Contabilidad Gubernamental. Artículo 46 fracción XII, 55 y 74 de la Ley de Obras Públicas y Servicios Relacionados con la Mismas."
  },
  {
    "tipo": "Pago de obras sin acreditar propiedad del bien inmueble",
    "descripcion_irregularidad": "Por contrato / Administración Directa: Recuros destinados al financimiento de obras o acciones que sin acreditan la propiedad del bien inmueble donde se ejecutaron los trabajos.",
    "accion_promovida": "Pliego de Observaciones (PO) / Probable Daño Patrimonial (PDP)",
    "acciones_irregularidad": [
      "Ejecución de obras o acciones sin contar con documentación legal que acredite la propiedad."
    ],
    "documentacion_soporte": [
      "Copia certificada de la cuenta pública del ente fiscalizado de los conceptos observados: Pólizas contables, Facturas, Contrato y convenio modificatorio, Acta entrega recepción del municipio a los beneficiarios.",
      "Documentación integrada por el ente auditor: Levantamiento físico (croquis y/o planos), Reporte fotográfico, Acta de auditoria donde consten los hechos observados."
    ],
    "normatividad_local_administracion_directa": "Artículos 25, 27, 83, de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_local_contrato": "Artículos 25, 27, 83, de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_federal_administracion_directa": "Artículo 19, 52, 65, de la Ley de Obras Públicas y Servicios Relacionados con la Mismas.",
    "normatividad_federal_contratacion": "Artículo 19, 52, 65, de la Ley de Obras Públicas y Servicios Relacionados con la Mismas."
  },
  {
    "tipo": "Concepto pagado que no cumple con especificaciones ténicas estimadas",
    "descripcion_irregularidad": "Es el concepto de obra ejecutado, si embargo, no cumple con las especificciones técnicas descritas en el catalogo de conceptos contatado y estimado. Lo que resulta una inversión menor en la cantidad de material y en consecuencia no cumplir can la vida util de la obra de proyecto.",
    "accion_promovida": "Probable Daño Patrimonial (PDP)",
    "acciones_irregularidad": [
      "Simulación de documentación técnica justificativa, toda vez, que los trabajos no han sido ejecutado cumpliendo especificaciones técnicas.",
      "Dosificación menor de insumos que integran el concepto de obra.",
      "Disminución de dimenciones en la ejecución del concepto."
    ],
    "documentacion_soporte": [
      "Copia certificada de la cuenta pública del ente fiscalizado de los conceptos observados: Orden de pago, Pólizas contables, Transferencias, Presupuesto (catálogo de conceptos contratados), Contrato y convenio modificatorio, Facturas, estimaciones, números generadores, Bitácora de obra, Reporte fotográfico, Acta entrega recepción.",
      "Documentación integrada por el ente auditor: Levantamiento físico (croquis y/o planos), Cédula de cálculos realizados, Reporte fotográfico, Pruebas de Laboratorio de obra."
    ],
    "normatividad_local_administracion_directa": "Artículos 10, 74, 75, 76, 77 de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_local_contrato": "Artículos 58, 59, 60 de la Ley de Obras Públicas para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_federal_administracion_directa": "Artículos 70, 71, 72 y 73 de la Ley de Obras Públicas y Servicios Relacionados con la Mismas.",
    "normatividad_federal_contratacion": "Artículo 46 fracción XII, 53 y 55 de la Ley de Obras Públicas y Servicios Relacionados con la Mismas. Artículo 131 del Reglamento de la Ley de Obras Públicas y Servicios Relacionados con la Mismas."
  }
]'''

_FINANCIERO_JSON = r'''[
  {
    "tipo": "Manuales de org y proce Reglamento de control interno",
    "descripcion_irregularidad": "Falta de manuales de organización y procedimientos o reglamento de control interno actualizado",
    "accion_promovida": "Observación por incumplimiento normativo",
    "acciones_irregularidad": [
      "No contar con manuales de organización y procedimientos actualizados",
      "Carecer de reglamento de control interno vigente",
      "Incumplimiento en la implementación de controles internos"
    ],
    "documentacion_soporte": [
      "Copia de manuales de organización y procedimientos",
      "Reglamento de control interno",
      "Acta de actualización de documentos normativos",
      "Evidencia de implementación de controles"
    ],
    "normatividad_local": "Artículos 21, 27 párrafo segundo, 34 fracción XI, XIII y décimo séptimo transitorio de la Ley Orgánica de la Administración Pública del Estado de Tlaxcala, 3, 3, 9, 13 y 18 fracción IV de los Lineamientos Generales de Control Interno y sus Normas de Aplicación para la Administración Pública Estatal.",
    "normatividad_federal": "Ley General de Contabilidad Gubernamental en materia de control interno"
  },
  {
    "tipo": "No presentan pólizas",
    "descripcion_irregularidad": "Omisión en la presentación de pólizas contables requeridas para la fiscalización",
    "accion_promovida": "Observación por falta de documentación",
    "acciones_irregularidad": [
      "No presentar pólizas contables solicitadas",
      "Documentación contable incompleta",
      "Incumplimiento en la entrega de información fiscal"
    ],
    "documentacion_soporte": [
      "Lista de pólizas requeridas",
      "Oficios de solicitud de información",
      "Acta de entrega-recepción de documentación",
      "Constancia de incumplimiento"
    ],
    "normatividad_local": "Artículos 15 y 18 de la Ley de Fiscalización Superior y Rendición de Cuentas del Estado de Tlaxcala y sus Municipios, 302 del Código Financiero para el Estado de Tlaxcala, 93 fracción VIII y 107 fracción VI del Presupuesto de Egresos del Estado de Tlaxcala para el Ejercicio Fiscal 2024, 20 fracción XIII del Acuerdo que Establece los Lineamientos y Políticas Generales del Ejercicio del Presupuesto.",
    "normatividad_federal": "Ley General de Contabilidad Gubernamental en materia de documentación comprobatoria"
  },
  {
    "tipo": "Saldos Contrarios a su naturaleza",
    "descripcion_irregularidad": "Existencia de saldos contables que no corresponden a la naturaleza de las cuentas",
    "accion_promovida": "Observación contable",
    "acciones_irregularidad": [
      "Saldos en cuentas que no corresponden a su naturaleza contable",
      "Registros contables inconsistentes",
      "Incumplimiento de postulados básicos de contabilidad gubernamental"
    ],
    "documentacion_soporte": [
      "Estado de situación financiera",
      "Balances de comprobación",
      "Catálogo de cuentas",
      "Notas a los estados financieros"
    ],
    "normatividad_local": "Artículos 2, 16, 17, 19 fracciones II y V, 33, 34, 37 y 44 de la Ley General de Contabilidad Gubernamental, 302 del Código Financiero para el Estado de Tlaxcala y sus Municipios, 1 párrafos sexto, séptimo y 152 del Presupuesto de Egresos del Estado de Tlaxcala para el Ejercicio Fiscal 2025.",
    "normatividad_federal": "Postulados Básicos de Contabilidad Gubernamental de 'Revelación Suficiente' e 'Importancia Relativa'"
  },
  {
    "tipo": "Cuentas por cobrar pendientes",
    "descripcion_irregularidad": "Cuentas por cobrar pendientes de gestión y recuperación",
    "accion_promovida": "Observación por gestión de cobranza",
    "acciones_irregularidad": [
      "Falta de gestión activa de cuentas por cobrar",
      "Plazos vencidos sin acción de cobro",
      "Incumplimiento en políticas de recuperación"
    ],
    "documentacion_soporte": [
      "Estado de cuentas por cobrar",
      "Gestión de cobranza documentada",
      "Políticas de crédito y cobranza",
      "Edades de saldos pendientes"
    ],
    "normatividad_local": "Artículos 43 de la Ley General de Contabilidad Gubernamental, 302 del Código Financiero para el Estado de Tlaxcala y sus Municipios, 152 del Presupuesto de Egresos del Estado de Tlaxcala para el Ejercicio Fiscal 2025 y 8 del Acuerdo que establece los Lineamientos y Políticas Generales del Ejercicio del Presupuesto.",
    "normatividad_federal": "Ley General de Contabilidad Gubernamental en materia de activos"
  },
  {
    "tipo": "Ingresos no registrados",
    "descripcion_irregularidad": "Ingresos percibidos que no fueron registrados contablemente",
    "accion_promovida": "Probable Daño Patrimonial (PDP)",
    "acciones_irregularidad": [
      "Omisión en el registro de ingresos percibidos",
      "Falta de integración presupuestaria",
      "Incumplimiento de principios contables"
    ],
    "documentacion_soporte": [
      "Estados bancarios",
      "Comprobantes de ingresos",
      "Conciliaciones bancarias",
      "Reportes de tesorería"
    ],
    "normatividad_local": "Artículos 134 párrafo primero de la Constitución Política de los Estados Unidos Mexicanos, 16, 17, 18, 19, 21, 22, 33, 34, 35, 36, 37, 38, 40, 41, y 44 de la Ley General de Contabilidad Gubernamental, 13 fracción IV de la Ley de Disciplina Financiera de las Entidades Federativas y los Municipios, 302, 305 y 309 del Código Financiero para el Estado de Tlaxcala y sus Municipios.",
    "normatividad_federal": "Postulados Básicos de Contabilidad Gubernamental: 'Revelación suficiente', 'Importancia relativa' y 'Registro e integración presupuestaria'"
  },
  {
    "tipo": "Ministración mayor federal",
    "descripcion_irregularidad": "Recepción de ministraciones federales superiores a lo programado",
    "accion_promovida": "Observación por conciliación de recursos",
    "acciones_irregularidad": [
      "Diferencias entre ministración recibida y programada",
      "Falta de conciliación con recursos federales",
      "Incumplimiento en el reporte de recursos federales"
    ],
    "documentacion_soporte": [
      "Acuerdo de distribución y calendarización de recursos federales",
      "Estados de cuenta de recursos federales",
      "Conciliaciones con TESOFE",
      "Reportes de ejercicio de recursos federales"
    ],
    "normatividad_local": "Artículos 292 del Código Financiero para el Estado de Tlaxcala y sus Municipios, Acuerdo por el que se da a conocer a los gobiernos de las entidades federativas la distribución y calendarización para la ministración durante el Ejercicio Fiscal 2024, 1 párrafos segundo, quinto y sexto, 13 y 150 del Presupuesto de Egresos del Estado de Tlaxcala para el Ejercicio Fiscal 2024.",
    "normatividad_federal": "Ley de Coordinación Fiscal y disposiciones de recursos federales"
  },
  {
    "tipo": "Inasistencias del personal",
    "descripcion_irregularidad": "Inasistencias del personal no justificadas o no registradas adecuadamente",
    "accion_promovida": "Observación por control de personal",
    "acciones_irregularidad": [
      "Falta de registro de inasistencias",
      "Inasistencias no justificadas",
      "Incumplimiento de controles de asistencia"
    ],
    "documentacion_soporte": [
      "Registros de asistencia",
      "Control de incidencias de personal",
      "Justificantes de inasistencias",
      "Reportes de nómina"
    ],
    "normatividad_local": "Artículos 134 párrafo primero de la Constitución Política de los Estados Unidos Mexicanos, 48 fracción V y 25 fracción III de la Ley Laboral de los Servidores Públicos del Estado de Tlaxcala y sus Municipios, 302 del Código Financiero para el Estado de Tlaxcala y sus Municipios, 1 párrafos segundo, quinto y sexto, 49, 54 fracción I y 150 del Presupuesto de Egresos del Estado de Tlaxcala para el Ejercicio Fiscal 2024.",
    "normatividad_federal": "Lineamientos para el Control, Registro y Aplicación de Incidencias de Personal"
  },
  {
    "tipo": "Personal que no realiza controles de asistencia",
    "descripcion_irregularidad": "Personal que no cumple con los controles de asistencia establecidos",
    "accion_promovida": "Observación por control administrativo",
    "acciones_irregularidad": [
      "Falta de registro de asistencia",
      "Incumplimiento de controles biométricos",
      "Omisión en el reporte de incidencias"
    ],
    "documentacion_soporte": [
      "Registros de control de asistencia",
      "Reportes de incidencias",
      "Políticas de control de personal",
      "Evidencia de cumplimiento de controles"
    ],
    "normatividad_local": "Artículos 48 fracción V y 25 fracción III de la Ley Laboral de los Servidores Públicos del Estado de Tlaxcala y sus Municipios, 302 del Código Financiero para el Estado de Tlaxcala y sus Municipios, 1 párrafos segundo, quinto y sexto, 49, 54 fracción I y 150 del Presupuesto de Egresos del Estado de Tlaxcala para el Ejercicio Fiscal 2023.",
    "normatividad_federal": "Disposiciones Generales y Lineamientos para el Control, Registro y Aplicación de Incidencias de Personal"
  }
]'''

AUDITORIA_DATA = {
    "Obra Pública": json.loads(_OBRA_PUBLICA_JSON),
    "Financiera": json.loads(_FINANCIERO_JSON),
}
