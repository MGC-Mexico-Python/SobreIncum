from flask import Flask, render_template

from src import Sobregiros
from mdb import PostgreSQL
import os
from dotenv import load_dotenv

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

    s = {
        'hoy': sobregiro.sobregiro_hoy() 
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