# Utility data and helpers for Auditel.
import json
import logging
import re
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

logger = logging.getLogger("auditel.utils")

_BASE_DIR = Path(__file__).resolve().parent.parent
_XML_NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "p": "http://schemas.openxmlformats.org/package/2006/relationships",
}

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


def _normalizar_valor_excel(valor):
    """Limpia texto leído desde celdas XLSX."""
    if valor is None:
        return ""

    texto = str(valor).replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _columna_a_indice(columna):
    indice = 0
    for caracter in columna:
        if caracter.isalpha():
            indice = indice * 26 + (ord(caracter.upper()) - 64)
    return indice


def _cargar_shared_strings(zip_file):
    shared_strings = []
    if "xl/sharedStrings.xml" not in zip_file.namelist():
        return shared_strings

    root = ET.fromstring(zip_file.read("xl/sharedStrings.xml"))
    for item in root.findall("a:si", _XML_NS):
        textos = [texto.text or "" for texto in item.iterfind(".//a:t", _XML_NS)]
        shared_strings.append("".join(textos))

    return shared_strings


def _leer_valor_celda(celda, shared_strings):
    tipo = celda.get("t")
    valor = celda.find("a:v", _XML_NS)
    if valor is None:
        inline = celda.find("a:is", _XML_NS)
        if inline is None:
            return ""
        textos = [texto.text or "" for texto in inline.iterfind(".//a:t", _XML_NS)]
        return "".join(textos)

    contenido = valor.text or ""
    if tipo == "s":
        try:
            return shared_strings[int(contenido)]
        except (ValueError, IndexError):
            return contenido

    return contenido


def _resolver_ruta_hoja(zip_file, sheet_name=None):
    workbook = ET.fromstring(zip_file.read("xl/workbook.xml"))
    relaciones = ET.fromstring(zip_file.read("xl/_rels/workbook.xml.rels"))
    mapa_relaciones = {
        relacion.get("Id"): relacion.get("Target")
        for relacion in relaciones.findall("p:Relationship", _XML_NS)
    }

    hojas = []
    nodo_hojas = workbook.find("a:sheets", _XML_NS)
    if nodo_hojas is None:
        return None

    for hoja in nodo_hojas:
        nombre = hoja.get("name")
        relacion_id = hoja.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        destino = mapa_relaciones.get(relacion_id)
        if nombre and destino:
            hojas.append((nombre, destino))

    if not hojas:
        return None

    if sheet_name:
        for nombre, destino in hojas:
            if nombre == sheet_name:
                return f"xl/{destino}" if not destino.startswith("xl/") else destino
        return None

    nombre, destino = hojas[0]
    return f"xl/{destino}" if not destino.startswith("xl/") else destino


def _leer_filas_xlsx(path, sheet_name=None, start_row=1):
    """Lee filas no vacías de un archivo XLSX sin dependencias externas."""
    if not path.exists():
        logger.warning("Fuente XLSX no encontrada: %s", path)
        return []

    with ZipFile(path) as zip_file:
        shared_strings = _cargar_shared_strings(zip_file)
        sheet_path = _resolver_ruta_hoja(zip_file, sheet_name=sheet_name)
        if not sheet_path:
            logger.warning("Hoja no encontrada en %s: %s", path.name, sheet_name)
            return []

        root = ET.fromstring(zip_file.read(sheet_path))
        filas = []

        for fila in root.findall(".//a:sheetData/a:row", _XML_NS):
            numero_fila = int(fila.get("r", "0"))
            if numero_fila < start_row:
                continue

            celdas = {}
            for celda in fila.findall("a:c", _XML_NS):
                referencia = celda.get("r", "")
                columna = "".join(caracter for caracter in referencia if caracter.isalpha())
                indice = _columna_a_indice(columna)
                celdas[indice] = _normalizar_valor_excel(_leer_valor_celda(celda, shared_strings))

            if not celdas:
                continue

            max_columna = max(celdas)
            valores = [celdas.get(indice, "") for indice in range(1, max_columna + 1)]

            if any(valor for valor in valores):
                filas.append((numero_fila, valores))

        return filas


def _cargar_fuente_financiera_excel():
    """Carga la fuente adicional de conceptos normativos de auditoría financiera."""
    path = _BASE_DIR / "Financiero" / "Normatividad.xlsx"
    registros = []

    for _, fila in _leer_filas_xlsx(path, sheet_name="Normatividad", start_row=2):
        concepto = fila[1] if len(fila) > 1 else ""
        normativa = fila[2] if len(fila) > 2 else ""

        if not concepto or not normativa:
            continue

        registros.append({
            "tipo": concepto,
            "concepto": concepto,
            "descripcion_irregularidad": "",
            "normatividad_local": normativa,
            "normatividad_federal": "",
            "origen_fuente": "excel_financiero_conceptos",
            "archivo_fuente": path.name,
        })

    return registros


def _cargar_fuente_obra_publica_excel():
    """Carga la fuente adicional de obra pública basada en concepto y normativa."""
    path = _BASE_DIR / "Obra Pública" / "Base_2025_Entes_Estatales_con_anexo_vinculado.xlsx"
    registros = []

    for _, fila in _leer_filas_xlsx(path, sheet_name="Irregularidades", start_row=3):
        tipo = fila[0] if len(fila) > 0 else ""
        descripcion = fila[1] if len(fila) > 1 else ""
        concepto = fila[5] if len(fila) > 5 else ""
        norm_local_admin = fila[10] if len(fila) > 10 else ""
        norm_local_contrato = fila[11] if len(fila) > 11 else ""
        norm_federal_admin = fila[15] if len(fila) > 15 else ""
        norm_federal_contratacion = fila[16] if len(fila) > 16 else ""

        if not tipo and not concepto:
            continue

        if not any([norm_local_admin, norm_local_contrato, norm_federal_admin, norm_federal_contratacion]):
            continue

        registros.append({
            "tipo": tipo,
            "concepto": concepto,
            "descripcion_irregularidad": descripcion,
            "normatividad_local_administracion_directa": norm_local_admin,
            "normatividad_local_contrato": norm_local_contrato,
            "normatividad_federal_administracion_directa": norm_federal_admin,
            "normatividad_federal_contratacion": norm_federal_contratacion,
            "origen_fuente": "excel_obra_publica_conceptos",
            "archivo_fuente": path.name,
        })

    return registros


def _construir_auditoria_data():
    auditoria_data = {
        "Obra Pública": json.loads(_OBRA_PUBLICA_JSON),
        "Financiera": json.loads(_FINANCIERO_JSON),
    }

    fuentes_adicionales = {
        "Obra Pública": _cargar_fuente_obra_publica_excel(),
        "Financiera": _cargar_fuente_financiera_excel(),
    }

    for auditoria, registros in fuentes_adicionales.items():
        if registros:
            auditoria_data.setdefault(auditoria, []).extend(registros)
            logger.info(
                "Se agregaron %s registros adicionales a %s desde fuentes XLSX",
                len(registros),
                auditoria,
            )

    return auditoria_data

AUDITORIA_DATA = _construir_auditoria_data()
