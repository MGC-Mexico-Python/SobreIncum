from mdb import PostgreSQL
import pandas as pd
from utils import Calendario
from utils import money


class Incumplimientos():

    def __init__(self,
                 conexion: PostgreSQL
                 ):

        self.conexion = conexion

    # ------------------------------------------------------------------
    # Dashboard principal
    # ------------------------------------------------------------------

    def incumplimiento_hoy(self):

        query = self.conexion.consultar('''
        SELECT
            "Interlocutor",
            "Razon Social",
            "Límite de credito",
            "Importe de la garantía",
            "Monto vencimiento"
        FROM "Vencimientos"
        WHERE "Fecha" = (SELECT
                            MAX("Fecha")
                         FROM "Vencimientos")
        AND "Interlocutor" LIKE 'F%'
        AND "Condiciones de pago" LIKE 'CP%'
        ''')

        query['Money Límite de credito']      = money(query['Límite de credito'])
        query['Money Importe de la garantía'] = money(query['Importe de la garantía'])
        query['Money Monto vencimiento']      = money(query['Monto vencimiento'])

        query = query.to_dict(orient='records')

        return query

    def incumplimiento_ayer(self):

        query = self.conexion.consultar('''
        SELECT
            "Interlocutor",
            "Razon Social",
            "Límite de credito",
            "Importe de la garantía",
            "Monto vencimiento"
        FROM "Vencimientos"
        WHERE "Fecha" = (SELECT
                            MAX("Fecha")
                         FROM "Vencimientos"
                         WHERE "Fecha" < (SELECT
                                            MAX("Fecha")
                                          FROM "Vencimientos"))
        AND "Interlocutor" LIKE 'F%'
        AND "Condiciones de pago" LIKE 'CP%'
        ''')

        query['Money Límite de credito']      = money(query['Límite de credito'])
        query['Money Importe de la garantía'] = money(query['Importe de la garantía'])
        query['Money Monto vencimiento']      = money(query['Monto vencimiento'])

        query = query.to_dict(orient='records')

        return query

    def hoy_vs_ayer(self):

        hoy  = pd.DataFrame(self.incumplimiento_hoy())
        ayer = pd.DataFrame(self.incumplimiento_ayer())

        hoy_clientes = len(hoy)
        hoy_monto    = money(hoy['Monto vencimiento'].sum())

        diff_clientes = hoy_clientes - len(ayer)
        diff_montos   = money(hoy['Monto vencimiento'].sum() - ayer['Monto vencimiento'].sum())

        return {
            'clientes'      : hoy_clientes,
            'monto'         : hoy_monto,
            'diff_clientes' : diff_clientes,
            'diff_monto'    : diff_montos
        }

    def incumplimiento_semana(self):

        query = self.conexion.consultar('''
        SELECT
            "Interlocutor",
            "Razon Social",
            "Límite de credito",
            "Importe de la garantía",
            "Monto vencimiento",
            "Fecha"
        FROM "Vencimientos"
        WHERE "Fecha" >= DATE_TRUNC('week', CURRENT_DATE)
        AND "Interlocutor" LIKE 'F%'
        AND "Condiciones de pago" LIKE 'CP%'
        ''',
        parse_dates='Fecha')

        query['Fecha'] = query['Fecha'].dt.strftime('%A').str.title()

        query = query.groupby(['Fecha'], as_index=False)['Monto vencimiento'].sum()

        dias_orden = {
            'Lunes': 1, 'Martes': 2, 'Miércoles': 3, 'Jueves': 4, 'Viernes': 5
        }

        query['Orden'] = query['Fecha'].map(dias_orden)
        query = query.sort_values('Orden').drop('Orden', axis=1)

        query['Money Monto vencimiento'] = money(query['Monto vencimiento'])
        query['Monto vencimiento']       = round(query['Monto vencimiento'], 2)

        query = query.to_dict(orient='records')

        return query

    def lista_incumplimientos(self):

        query = self.conexion.consultar('''
        SELECT
            "Interlocutor",
            "Razon Social"
        FROM "Vencimientos"
        WHERE "Fecha" >= (DATE_TRUNC(
                            'month', CURRENT_DATE)
                            - INTERVAL '5 months')
        AND "Interlocutor" LIKE 'F%'
        AND "Condiciones de pago" LIKE 'CP%'
        GROUP BY "Interlocutor", "Razon Social"
        ''',
        output='dict')

        return query

    # ------------------------------------------------------------------
    # Vista individual — análisis y score
    # ------------------------------------------------------------------

    def _analisis_cliente(self,
                      query: pd.DataFrame,
                      cliente
                      ) -> dict:

        fila_hoy = query[query['Fecha'] == query['Fecha'].max()].iloc[0]

        hoy = self.datos_hoy(cliente)

        if not hoy:
            raise ValueError(f'No se encontraron datos para el cliente {cliente}')

        hoy = hoy[0]

        datos = {
            'nombre'  : hoy['Razon Social'],
            'cp'      : hoy['Condiciones de pago'],
            'limite'  : money(hoy['Límite de credito']),
            'garantia': money(hoy['Importe de la garantía']),
            'monto'   : money(fila_hoy['Monto vencimiento']
                            if fila_hoy['Fecha'].normalize() == pd.Timestamp.today().normalize()
                            else 0)
        }

        if len(query) <= 3:
            return {
                'valido'  : False,
                'mensaje' : 'El cliente no tiene suficientes datos para un análisis de sus vencimientos.',
                'eventos' : len(query),
                'datos'   : datos
            }

        query = query.copy().sort_values('Fecha')

        # --- Tendencia del monto (40%) ---
        # Promedio de los primeros 2 meses vs últimos 2 meses de la ventana.
        # Monto acumulado: si sube = más deuda vencida (malo), si baja = pagando (bueno).
        periodos = query['Fecha'].dt.to_period('M').sort_values().unique()

        if len(periodos) >= 4:
            prom_inicio = query[query['Fecha'].dt.to_period('M').isin(periodos[:2])]['Monto vencimiento'].mean()
            prom_fin    = query[query['Fecha'].dt.to_period('M').isin(periodos[-2:])]['Monto vencimiento'].mean()

            if prom_inicio == 0:
                ratio_tendencia = 1.0
            else:
                cambio          = (prom_fin - prom_inicio) / prom_inicio
                ratio_tendencia = round(min(max((cambio + 1) / 2, 0), 1), 2)
        else:
            ratio_tendencia = 0.5

        # --- Variación entre registros (30%) ---
        # Delta del monto entre registros consecutivos.
        # Promedio de deltas positivos (acumula) vs negativos (abona).
        # Normalizado a [0, 1]: 1 = siempre sube, 0 = siempre baja.
        deltas = query['Monto vencimiento'].diff().dropna()

        if len(deltas) > 0:
            delta_max = deltas.abs().max()
            if delta_max == 0:
                ratio_variacion = 0.5
            else:
                ratio_variacion = round(
                    min(max((deltas.mean() / delta_max + 1) / 2, 0), 1), 2
                )
        else:
            ratio_variacion = 0.5

        # --- Concentración mensual (30%) ---
        # Meses con al menos un registro / 6 meses de ventana.
        # 6/6 = presente todos los meses (malo), 1/6 = episodio aislado (bueno).
        meses_con_registro = query['Fecha'].dt.to_period('M').nunique()
        ratio_concentracion = round(meses_con_registro / 6, 2)

        return {
            'valido'             : True,
            'ratio_tendencia'    : ratio_tendencia,
            'ratio_variacion'    : ratio_variacion,
            'ratio_concentracion': ratio_concentracion,
            'eventos'            : len(query),
            'datos'              : datos
        }

    def _score_incumplimiento(self,
                            analisis: dict
                            ) -> dict:

        score = round(
            (analisis['ratio_tendencia']    * 0.40
        + analisis['ratio_variacion']    * 0.30
        + analisis['ratio_concentracion']* 0.30),
            2
        )

        if score < 0.35:
            clasificacion = 'Puntual'
        elif score <= 0.65:
            clasificacion = 'Recurrente'
        else:
            clasificacion = 'Crítico'

        tend = 'creciente' if analisis['ratio_tendencia'] > 0.5 else 'decreciente'
        conc = round(analisis['ratio_concentracion'] * 100, 1)

        if clasificacion == 'Puntual':
            mensaje = (
                f'<strong>Comportamiento: Puntual</strong><br><br>'
                f'Presente en <strong>{conc}%</strong> de los últimos 6 meses, '
                f'con monto acumulado <strong>{tend}</strong>.<br><br>'
                f'Los retrasos son esporádicos y el cliente muestra capacidad de regularizar. '
                f'No representa un riesgo activo.<br><br>'
                f'<em>Acción:</em> Monitoreo estándar, sin cambios en condiciones de crédito.'
            )

        elif clasificacion == 'Recurrente':
            mensaje = (
                f'<strong>Comportamiento: Recurrente</strong><br><br>'
                f'Presente en <strong>{conc}%</strong> de los últimos 6 meses, '
                f'con monto acumulado <strong>{tend}</strong>.<br><br>'
                f'El cliente abona pero no regulariza de forma sostenida, '
                f'manteniendo deuda vencida activa de manera intermitente.<br><br>'
                f'<em>Acción:</em> Seguimiento activo. Evaluar si las condiciones de pago '
                f'siguen siendo adecuadas.'
            )

        else:
            mensaje = (
                f'<strong>Comportamiento: Crítico</strong><br><br>'
                f'Presente en <strong>{conc}%</strong> de los últimos 6 meses, '
                f'con monto acumulado <strong>{tend}</strong>.<br><br>'
                f'La deuda vencida se acumula sin reducción real entre cortes. '
                f'El riesgo de recuperación es alto.<br><br>'
                f'<em>Acción:</em> Escalar a crédito y cobranza de inmediato. '
                f'Considerar suspensión de crédito hasta regularización comprobable.'
            )

        return {
            'clasificacion': clasificacion,
            'mensaje'      : mensaje,
            'score'        : score
        }

    def incumplimiento_cliente(self, cliente):

        query = self.conexion.consultar('''
        SELECT
            "Interlocutor",
            "Razon Social",
            "Condiciones de pago",
            "Saldo",
            "Límite de credito",
            "Importe de la garantía",
            "Monto vencimiento",
            "Fecha",
            "Mes",
            "Año"
        FROM "Vencimientos"
        WHERE "Interlocutor" = :cliente
        AND "Fecha" >= (DATE_TRUNC(
                            'month', CURRENT_DATE)
                        - INTERVAL '5 months')
        ORDER BY "Fecha"
        ''',
        params={'cliente': cliente},
        parse_dates='Fecha')

        analisis = self._analisis_cliente(query, cliente)

        if analisis['valido']:
            score = self._score_incumplimiento(analisis)
        else:
            score = {'clasificacion': None, 'mensaje': analisis['mensaje'], 'score': None}

        # --- Gráfica semanal ---
        dias          = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
        query_semanal = query.copy()
        query_semanal['Fecha'] = query_semanal['Fecha'].dt.strftime('%A').str.title()

        graf_semanal_monto = query_semanal.groupby(
            ['Fecha'])['Monto vencimiento'].mean().reindex(dias, fill_value=0).reset_index()

        graf_semanal_eventos = query_semanal.groupby(
            ['Fecha'])['Interlocutor'].count().reindex(dias, fill_value=0).reset_index()

        # --- Gráfica mensual ---
        meses        = []
        fecha_actual = pd.to_datetime('today')

        for i in range(5, -1, -1):
            fecha = fecha_actual - pd.DateOffset(months=i)
            meses.append(fecha.strftime('%B').title())

        query_mensual = query.copy()
        query_mensual['Fecha'] = query_mensual['Fecha'].dt.strftime('%B').str.title()

        graf_mensual_monto = query_mensual.groupby(
            ['Fecha'])['Monto vencimiento'].mean().reindex(meses, fill_value=0).reset_index()

        graf_mensual_eventos = query_mensual.groupby(
            ['Fecha'])['Interlocutor'].count().reindex(meses, fill_value=0).reset_index()

        return {
            'historial'           : query,
            'graf_mensual_eventos': graf_mensual_eventos,
            'graf_semanal_eventos': graf_semanal_eventos,
            'graf_mensual_monto'  : graf_mensual_monto,
            'graf_semanal_monto'  : graf_semanal_monto,
            'datos'               : analisis,
            'mensaje'             : score
        }
    
    def excel_incumplimientos(self):

        query = self.conexion.consultar('''
        SELECT
            *
        FROM "Vencimientos"
        WHERE "Fecha" >= (DATE_TRUNC(
                            'month', CURRENT_DATE)
                            - INTERVAL '5 months')
        AND "Interlocutor" LIKE 'F%'
        AND "Condiciones de pago" LIKE 'CP%'
        ORDER BY "Fecha", "Interlocutor"
        ''')

        return query
    
    def datos_hoy(self, cliente):

        query = self.conexion.consultar('''
        SELECT
            "Interlocutor",
            "Razon Social",
            "Condiciones de pago",
            "Límite de credito",
            "Importe de la garantía"
        FROM "Vencimientos"
        WHERE "Fecha" = (
            SELECT MAX("Fecha")
            FROM "Vencimientos"
            WHERE "Interlocutor" = :cliente
        )
        AND "Interlocutor" = :cliente
        ''',
        params = {'cliente': cliente},
        output = 'dict')

        return query