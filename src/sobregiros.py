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

        monto_hoy = money(fila_hoy['Monto sobregiro'] if fila_hoy['Fecha'].normalize() == pd.Timestamp.today().normalize() else 0)
        nombre    = fila_hoy['Razon Social']
        cp        = fila_hoy['Condiciones de pago']
        limite    = money(fila_hoy['Límite de credito'])
        garantia  = money(fila_hoy['Importe de la garantía'])

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
                'eventos': len(query),
                'datos': datos
            }
        
        query['Condiciones de pago'] = pd.to_numeric(query['Condiciones de pago'].str[2:])
        query['Dias sin sobregiro'] =  Calendario.diferencia_habil(query['Fecha'])
        
        query['Ratio recurrencia'] = round(query['Dias sin sobregiro'] / query['Condiciones de pago'], 2).clip(upper = 1)
        query['Ratio monto'] =       round(query['Monto sobregiro'] / query['Límite de credito'], 2)
        

        return {
            'valido':            True,
            'ratio_permanencia': (query['Dias sin sobregiro'] == 0).sum() / len(query),
            'ratio_recurrencia': round(query['Ratio recurrencia'].mean(), 2),
            'ratio_monto':       round(query['Ratio monto'].mean(), 2),
            'eventos':           len(query),
            'datos':             datos
        }
    
    def _score_sobregiro(self, 
                         datos: dict
                         ) ->  dict:
        
        score = round(
            (datos['ratio_permanencia'] * 0.40
            + (1 - datos['ratio_recurrencia']) * 0.35
            + datos['ratio_monto'] * 0.25),
            2
        )

        if score <= 0.40:
            clasificacion = 'Operacional'

        elif score <= 0.60:
            clasificacion = 'Estratégico'

        else:
            clasificacion = 'Estructural'

        if clasificacion == 'Operacional':
            mensaje = f'''<strong>Comportamiento: Operacional</strong>

            Los eventos son aislados y muestran recuperación rápida entre episodios. 
            La permanencia en sobregiro es de {round(datos['ratio_permanencia'] * 100, 1)}% y el monto promedio representa {round(datos['ratio_monto'] * 100, 1)}% sobre su línea de crédito.
            
            El comportamiento sugiere tensiones temporales de liquidez sin dependencia continua del financiamiento de corto plazo.'''

        elif clasificacion == 'Estratégico':
            mensaje = f'''<strong>Comportamiento: Estratégico</strong>

            Se observan periodos frecuentes de permanencia en sobregiro y una recuperación parcial entre eventos. 
            La permanencia alcanza {round(datos['ratio_permanencia'] * 100, 1)}% y el monto promedio representa {round(datos['ratio_monto'] * 100, 1)}% sobre su línea de crédito.
            
            Aunque el cliente logra recuperar posición en determinados periodos, existe una dependencia recurrente de liquidez operativa.'''

        else:
            mensaje = f'''<strong>Comportamiento: Estructural</strong>

            La recuperación operativa entre eventos es limitada y el cliente mantiene una permanencia elevada en sobregiro. 
            La permanencia alcanza {round(datos['ratio_permanencia'] * 100, 1)}% y el monto promedio representa {round(datos['ratio_monto'] * 100, 1)}% sobre su línea de crédito.
            
            El perfil refleja una dependencia estructural del financiamiento de corto plazo y un riesgo elevado de sostenibilidad operativa.'''

        return {
            'clasificación': clasificacion,
            'mensaje': mensaje.strip()
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

        if analisis['valido'] == True:

            score = self._score_sobregiro(analisis)

        else:
            score = analisis['mensaje']

        query_semanal = query.copy()

        # Query semanal

        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

        query_semanal['Fecha'] = query_semanal['Fecha'].dt.strftime('%A').str.title()

        query_semanal_monto = query_semanal.groupby(
            ['Fecha'])['Monto sobregiro'].mean().reindex(dias, fill_value= 0).reset_index()

        query_semanal_eventos = query_semanal.groupby(
            ['Fecha'])['Interlocutor'].count().reindex(dias, fill_value= 0).reset_index()

        #Query mensual

        meses = []

        fecha_actual = pd.to_datetime('today')

        for i in range(5, -1, -1):

            fecha = fecha_actual - pd.DateOffset(months= i)

            meses.append(fecha.strftime('%B').title())

        query_mensual = query.copy()

        query_mensual['Fecha'] = query_mensual['Fecha'].dt.strftime('%B').str.title()
        
        query_mensual_monto = query_mensual.groupby(
            ['Fecha'])['Monto sobregiro'].mean().reindex(meses, fill_value=0).reset_index()

        query_mensual_eventos = query_mensual.groupby(
            ['Fecha'])['Interlocutor'].count().reindex(meses, fill_value=0).reset_index()

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
        AND "Interlocutor" LIKE 'F%'
        AND "Condiciones de pago" LIKE 'CP%'
        AND "Condiciones de pago" <> 'CP00'
        GROUP BY "Interlocutor", "Razon Social"
        ''',
        output= 'dict')

        return query
    
    def excel_sobregiros(self):

        query = self.conexion.consultar('''
        SELECT
            *
        FROM "Sobregiros"
        WHERE "Fecha" >= (DATE_TRUNC(
                            'month', CURRENT_DATE)
                            - INTERVAL '5 months')
        AND "Interlocutor" LIKE 'F%'
        AND "Condiciones de pago" LIKE 'CP%'
        AND "Condiciones de pago" <> 'CP00'
        ORDER BY "Fecha", "Interlocutor"
        ''')

        return query