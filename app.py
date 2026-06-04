from flask import Flask, render_template

from src import Sobregiros
from mdb import PostgreSQL

import os
from dotenv import load_dotenv
import locale

try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'spanish')

load_dotenv()

psql = PostgreSQL(host     = os.getenv('PSQL_host'),
                  database = os.getenv('PSQL_ReporteGarantia'),
                  user     = os.getenv('PSQL_user'),
                  password = os.getenv('PSQL_password'))
psql.conectar()

sobregiro = Sobregiros(psql)

app = Flask(__name__)

@app.route('/')
def sobregiros():

    tarjetas = sobregiro.hoy_vs_ayer()

    s = {
        'hoy'           : sobregiro.sobregiro_hoy(),
        'monto'         : tarjetas['monto'],
        'clientes'      : tarjetas['clientes'],
        'diff_monto'    : tarjetas['diff_monto'],
        'diff_clientes' : tarjetas['diff_clientes'],
        'semana'        : sobregiro.sobregiro_semana()
    }

    return render_template(
        'sobregiros.html',
        s = s
    )

@app.route('/cliente/<interlocutor>')
def cliente(interlocutor):

    return f'Cliente: {interlocutor}'

if __name__ == '__main__':

    app.run(debug=True)