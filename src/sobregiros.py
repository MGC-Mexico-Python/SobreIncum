from mdb import PostgreSQL
import pandas as pd
from utils import 


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
    
    def _analisis_cliente(
            query: pd.DataFrame
            ) -> dict:
        
        if len(query) <= 3:
            return '''El cliente no tiene suficientes datos para un análisis de sus sobregiros.'''
        
        query['Condiciones de pago'] = pd.to_numeric(query['Condiciones de pago'].str[2:])

        query['Dias entre sobregiros'] = query['Fecha'].diff().dt.days
        query['Uso de línea'] = round(query['Saldo'] / query['Límite de credito'], 2)        
    
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

        return query