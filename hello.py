from flask import Flask
from flask import request
from flask import url_for
from flask import redirect
from flask import render_template
from anime import df_exploded, predict_score_knn, gerar_graficos_dashboard

# Inicialização do Flask
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Visualização dos dados
@app.route('/dashboard')
def dashboard():
    graficos = gerar_graficos_dashboard()
    return render_template('dashboard.html', **graficos)

# Preditor de nota baseado em generos e numero de membros
generos_lista = df_exploded['Genres'].unique().to_list()
booleans = []
selecionados = []
membros = 0

@app.route('/escolhageneros', methods=['GET'])
def mostrar_generos():
    return render_template('generos.html', generos=generos_lista)

@app.route('/escolhageneros', methods=['POST'])
def processar_generos():
    global booleans, membros
    global selecionados
    selecionados = request.form.getlist('mostrar_generos')
    booleans = [g in selecionados for g in generos_lista]
    membros = int(request.form.get('membros', 0))
    return redirect(url_for('mostrar_resultados'))

@app.route('/resultados')
def mostrar_resultados():
    predicao = predict_score_knn(membros, booleans)
    print(predicao)
    return render_template('generos_selecionados.html', selecionados=selecionados, membros=membros, predição =predicao)

# rodar o servidor Flask
if __name__ == '__main__':
    app.run(debug=True)