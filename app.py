from flask import Flask, render_template, jsonify, send_file

from src import Sobregiros, Incumplimientos
from mdb import PostgreSQL

import pandas as pd 
import os
import io
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

sobregiro      = Sobregiros(psql)
incumplimiento = Incumplimientos(psql)

app = Flask(__name__)

@app.route('/')
@app.route('/sobregiros')
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

@app.route('/api/sobregiros/exportar')
def exportar_sobregiros():

    df = sobregiro.excel_sobregiros()
    
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='sobregiros.xlsx'
    )

# ------------------------------------------------------------------
# Incumplimientos
# ------------------------------------------------------------------

@app.route('/incumplimientos')
def incumplimientos():

    tarjetas = incumplimiento.hoy_vs_ayer()

    s = {
        'hoy'           : incumplimiento.incumplimiento_hoy(),
        'monto'         : tarjetas['monto'],
        'clientes'      : tarjetas['clientes'],
        'diff_monto'    : tarjetas['diff_monto'],
        'diff_clientes' : tarjetas['diff_clientes'],
        'semana'        : incumplimiento.incumplimiento_semana()
    }
    clientes = incumplimiento.lista_incumplimientos()

    return render_template(
        'incumplimientos.html',
        s = s,
        lista = clientes
    )

@app.route('/incumplimientos/cliente/<interlocutor>')
def cliente_incumplimiento(interlocutor):

    cliente_i = incumplimiento.incumplimiento_cliente(interlocutor)
    cliente_i['Interlocutor'] = interlocutor

    return render_template(
        'incumplimientos_cliente.html',
        s = cliente_i
    )

@app.route('/api/incumplimientos/cliente/<interlocutor>')
def api_cliente_incumplimiento(interlocutor):
    datos_hoy = incumplimiento.incumplimiento_hoy()
    resultado = [r for r in datos_hoy if r.get('Interlocutor') == interlocutor]
    return jsonify(resultado if resultado else {})

@app.route('/api/incumplimientos/exportar')
def exportar_incumplimientos():

    df = incumplimiento.excel_incumplimientos()
    
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='incumplimientos.xlsx'
    )


if __name__ == '__main__':
    from waitress import serve
    
    serve(app, host='0.0.0.0', port=8080)