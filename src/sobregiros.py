from mdb import PostgreSQL
import pandas as pd
from utils import Calendario
from utils import money

class Sobregiros():

    def __init__(self,
                 conexion: PostgreSQL
                 ):
        
        self.conexion = conexion

    def sobregiro_hoy(self):

        query = self.conexion.consultar('''
        SELECT
            "Interlocutor",
            "Razon Social",
            "Límite de credito",
            "Importe de la garantía",
            "Monto sobregiro"
        FROM "Sobregiros"
        WHERE "Fecha" = (SELECT
                            MAX("Fecha")
                         FROM "Sobregiros")
        AND "Interlocutor" LIKE 'F%'
        AND "Condiciones de pago" <> 'CP00'
        AND "Condiciones de pago" LIKE 'CP%'
        ''')

        query['Money Límite de credito']      = money(query['Límite de credito'])
        query['Money Importe de la garantía'] = money(query['Importe de la garantía'])
        query['Money Monto sobregiro']        = money(query['Monto sobregiro'])

        query = query.to_dict(orient = 'records')

        return query
    
    def sobregiro_ayer(self):

        query = self.conexion.consultar('''
        SELECT
            "Interlocutor",
            "Razon Social",
            "Límite de credito",
            "Importe de la garantía",
            "Monto sobregiro"
        FROM "Sobregiros"
        WHERE "Fecha" = (SELECT
                            MAX("Fecha")
                         FROM "Sobregiros"
                         WHERE "Fecha" < (SELECT
                                            MAX("Fecha")
                                          FROM "Sobregiros"))
        AND "Interlocutor" LIKE 'F%'
        AND "Condiciones de pago" <> 'CP00'
        AND "Condiciones de pago" LIKE 'CP%'
        ''')

        query['Money Límite de credito']      = money(query['Límite de credito'])
        query['Money Importe de la garantía'] = money(query['Importe de la garantía'])
        query['Money Monto sobregiro']        = money(query['Monto sobregiro'])

        query = query.to_dict(orient = 'records')

        return query

    def hoy_vs_ayer(self):

        hoy  = pd.DataFrame(self.sobregiro_hoy())
        ayer = pd.DataFrame(self.sobregiro_ayer())

        hoy_clientes = len(hoy)
        hoy_monto = money(hoy['Monto sobregiro'].sum())

        diff_clientes = hoy_clientes - len(ayer)
        diff_montos   = money(hoy['Monto sobregiro'].sum() - ayer['Monto sobregiro'].sum())

        return{
            'clientes'      : hoy_clientes,
            'monto'         : hoy_monto,
            'diff_clientes' : diff_clientes,
            'diff_monto'    : diff_montos
        }
    
    def sobregiro_semana(self):

        query = self.conexion.consultar('''
        SELECT
            "Interlocutor",
            "Razon Social",
            "Límite de credito",
            "Importe de la garantía",
            "Monto sobregiro",
            "Fecha"
        FROM "Sobregiros"
        WHERE "Fecha" >= DATE_TRUNC('week', CURRENT_DATE)
        AND "Interlocutor" LIKE 'F%'
        AND "Condiciones de pago" <> 'CP00'
        AND "Condiciones de pago" LIKE 'CP%'
        ''',
        parse_dates = 'Fecha')

        query['Fecha'] = query['Fecha'].dt.strftime('%A').str.title()

        query = query.groupby(['Fecha'], as_index = False)['Monto sobregiro'].sum()

        dias_orden = {
            'Lunes': 1, 'Martes': 2, 'Miércoles': 3, 'Jueves': 4, 'Viernes': 5
        }

        query['Orden'] = query['Fecha'].map(dias_orden)

        query = query.sort_values('Orden').drop('Orden', axis = 1)

        query['Money Monto sobregiro'] = money(query['Monto sobregiro'])

        query['Monto sobregiro'] = round(query['Monto sobregiro'], 2)

        query = query.to_dict(orient = 'records')

        return query
    
    def _sin_sobregiro_cliente(self, 
                               cliente):
        
        query = self.conexion.consultar('''
        SELECT
            "Interlocutor",
            "Saldo",
            "Límite de credito",
            "Fecha"
        FROM gasolinas
        WHERE "Fecha" >= (DATE_TRUNC(
                            'month', CURRENT_DATE)
                        - INTERVAL '5 months')
        AND "Sobregiros" = 0
        AND "Interlocutor" = :cliente
        ''', 
        params = {'cliente': cliente})

        return query
    
    def _analisis_cliente(self,
            query: pd.DataFrame,
            cliente
            ) -> dict:
        
        fila_hoy = query[query['Fecha'] == query['Fecha'].max()].iloc[0]

        monto_hoy = fila_hoy['Monto sobregiro']
        nombre    = fila_hoy['Razon Social']
        cp        = fila_hoy['Condiciones de pago']
        limite    = fila_hoy['Límite de credito']
        garantia  = fila_hoy['Importe de la garantía']

        datos = {
            'monto': monto_hoy,
            'nombre': nombre,
            'cp': cp,
            'limite': limite,
            'garantia': garantia
        }
        
        if len(query) <= 3:
            return {
                'valido':  False,
                'mensaje': '''El cliente no tiene suficientes datos para un análisis de sus sobregiros.''',
                'datos': datos
            }
        
        sin_s = self._sin_sobregiro_cliente(cliente)
        
        query['Condiciones de pago'] = pd.to_numeric(query['Condiciones de pago'].str[2:])
        query['Dias sin sobregiro'] =  Calendario.diferencia_habil(query['Fecha'])

        sin_s['Ratio uso'] =         round(sin_s['Saldo'] / sin_s['Límite de credito'], 2)
        query['Ratio recurrencia'] = round(query['Dias sin sobregiro'] / query['Condiciones de pago'], 2).clip(upper = 1)
        query['Ratio monto'] =       round(query['Monto sobregiro'] / query['Límite de credito'], 2)

        return {
            'valido':            True,
            'ratio_uso':         round(sin_s['Ratio uso'].mean(), 2),
            'ratio_recurrencia': round(query['Ratio recurrencia'].mean(), 2),
            'ratio_monto':       round(query['Ratio monto'].mean(), 2),
            'eventos':           len(query),
            'datos':             datos
        }
    
    def _score_sobregiro(self, 
                         datos: dict
                         ) ->  dict:
        
        score = round(
            (datos['ratio_uso']
            + (1 - datos['ratio_recurrencia'])
            + datos['ratio_monto']) / 3,
            2
        )

        if score <= 0.35:
            clasificacion = 'Operacional'

        elif score <= 0.65:
            clasificacion = 'Estratégico'

        else:
            clasificacion = 'Estructural'

        if clasificacion == 'Operacional':

            mensaje = f'''
El cliente presenta un comportamiento operacional de sobregiros.

Los eventos observados parecen ser aislados y de baja recurrencia operativa. 
El cliente mantiene periodos saludables entre sobregiros, con un ratio promedio de recurrencia de {datos['ratio_recurrencia']}, lo que indica capacidad de recuperación dentro de sus ciclos normales de operación.

Adicionalmente, el nivel promedio de sobregiro representa {round(datos['ratio_monto'] * 100, 1)}% de su línea de crédito, mientras que el uso promedio de línea se mantiene en {round(datos['ratio_uso'] * 100, 1)}%.

El comportamiento observado sugiere tensiones temporales de liquidez más que una dependencia estructural del financiamiento.
'''
        elif clasificacion == 'Estratégico':

            mensaje = f'''
El cliente presenta un comportamiento estratégico de sobregiros.

Se observa una recurrencia moderada en los eventos de sobregiro, con un ratio promedio de recurrencia de {datos['ratio_recurrencia']}, lo que sugiere que el cliente incorpora parcialmente el uso de sobregiros dentro de su dinámica operativa habitual.

El monto promedio de sobregiro equivale al {round(datos['ratio_monto'] * 100, 1)}% de su línea de crédito, mientras que el uso promedio de línea alcanza {round(datos['ratio_uso'] * 100, 1)}%.

Aunque el cliente logra recuperar posición entre eventos, la frecuencia observada refleja una dependencia recurrente de liquidez que debe mantenerse bajo monitoreo.
'''
        else:

            mensaje = f'''
El cliente presenta un comportamiento estructural de sobregiros.

La recurrencia observada indica una recuperación limitada entre eventos, con un ratio promedio de recurrencia de {datos['ratio_recurrencia']}, reflejando una exposición prácticamente continua a sobregiros.

Asimismo, el monto promedio de sobregiro representa {round(datos['ratio_monto'] * 100, 1)}% de la línea de crédito autorizada y el uso promedio de línea alcanza {round(datos['ratio_uso'] * 100, 1)}%, evidenciando una presión financiera sostenida.

El comportamiento identificado sugiere una dependencia estructural del financiamiento de corto plazo y un perfil de riesgo elevado en términos de liquidez operativa.
'''
        return {
            'clasificación': clasificacion,
            'mensaje': mensaje
        }
        
    def sobregiro_cliente(self,
                          cliente):

        query = self.conexion.consultar('''
        SELECT
            "Interlocutor",
            "Razon Social",
            "Condiciones de pago",
            "Saldo",
            "Límite de credito",
            "Importe de la garantía",
            "Monto sobregiro",
            "Fecha",
            "Mes",
            "Año"
        FROM "Sobregiros"
        WHERE "Interlocutor" = :cliente
        AND "Fecha" >= (DATE_TRUNC(
                            'month', CURRENT_DATE)
                        - INTERVAL '5 months')
        ORDER BY "Fecha"
        ''',
        params = {'cliente': cliente},
        parse_dates = 'Fecha')

        analisis = self._analisis_cliente(query, cliente)

        if analisis['valido']:

            score = self._score_sobregiro(analisis)

        else:
            score = analisis['mensaje']

        query_semanal = query.copy()

        query_semanal['Fecha'] = query_semanal['Fecha'].dt.strftime('%A').str.title()

        query_semanal_monto = query_semanal.groupby(['Fecha'], as_index = False)['Monto sobregiro'].mean()

        query_semanal_eventos = query_semanal.groupby(['Fecha'], as_index = False)['Interlocutor'].count()

        query_mensual = query.copy()

        query_mensual['Fecha'] = query_mensual['Fecha'].dt.strftime('%b').str.title()

        query_mensual_monto = query_mensual.groupby(['Fecha'], as_index = False)['Monto sobregiro'].mean()

        query_mensual_eventos = query_mensual.groupby(['Fecha'], as_index = False)['Interlocutor'].count()

        return {
            'historial'            : query,
            'graf_mensual_eventos' : query_mensual_eventos,
            'graf_semanal_eventos' : query_semanal_eventos,
            'graf_mensual_monto'   : query_mensual_monto,
            'graf_semanal_monto'   : query_semanal_monto,
            'datos'                : analisis,
            'mensaje'              : score
        }
    
    def lista_sobregiros(self):

        query = self.conexion.consultar('''
        SELECT
            "Interlocutor",
            "Razon Social"
        FROM "Sobregiros"
        WHERE "Fecha" >= (DATE_TRUNC(
                            'month', CURRENT_DATE)
                            - INTERVAL '5 months')
        GROUP BY "Interlocutor", "Razon Social"
        ''',
        output= 'dict')

        return query