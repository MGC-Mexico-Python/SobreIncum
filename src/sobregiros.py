from mdb import PostgreSQL
import pandas as pd
from utils import Calendario

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
        ''', 
        output = 'dict')

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
        AND "Interlocutor" = %s
        ''', 
        params = (cliente,))

        return query
    
    def _analisis_cliente(self,
            query: pd.DataFrame,
            cliente
            ) -> dict:
        
        if len(query) <= 3:
            return {
                'valido':  False,
                'mensaje': '''El cliente no tiene suficientes datos para un análisis de sus sobregiros.'''
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
            'eventos':           len(query)
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
        WHERE "Interlocutor" = %s
        AND "Fecha" >= (DATE_TRUNC(
                            'month', CURRENT_DATE)
                        - INTERVAL '5 months')
        ORDER BY "Fecha"
        ''',
        params = (cliente,),
        parse_dates = 'Fecha')

        analisis = self._analisis_cliente(query, cliente)

        if analisis['valido']:

            score = self._score_sobregiro(analisis)

        return {
            'historial': query,
            'datos': analisis,
            'mensaje': score
        }