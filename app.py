from flask import Flask, render_template, jsonify

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
    clientes = sobregiro.lista_sobregiros()

    return render_template(
        'sobregiros.html',
        s = s,
        lista = clientes
    )

@app.route('/sobregiros/cliente/<interlocutor>')
def cliente(interlocutor):

    cliente_s = sobregiro.sobregiro_cliente(interlocutor)

    cliente_s['Interlocutor'] = interlocutor

    return render_template(
        'sobregiros_cliente.html',
        s = cliente_s
    )

@app.route('/api/cliente/<interlocutor>')
def api_cliente(interlocutor):
    datos_hoy = sobregiro.sobregiro_hoy()
    resultado = [r for r in datos_hoy if r.get('Interlocutor') == interlocutor]
    return jsonify(resultado if resultado else {})


if __name__ == '__main__':

    app.run(debug=True)