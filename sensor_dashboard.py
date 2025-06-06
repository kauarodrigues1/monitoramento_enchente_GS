# Importa as bibliotecas necessárias para o funcionamento do app Dash
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go  # Para gerar os gráficos interativos
import requests  # Para fazer requisições HTTP
from datetime import datetime
import pytz  # Para lidar com fusos horários

# Define o IP e a porta do serviço STH-Comet (responsável por armazenar dados históricos no FIWARE)
IP_ADDRESS = "20.55.28.240"
PORT_STH = 8666
DASH_HOST = "localhost"  # Altere para "0.0.0.0" se quiser acessar de fora da máquina

# Função que busca os últimos N registros do atributo 'distance' para um sensor específico
def get_distance_data(lastN):
    url = f"http://{IP_ADDRESS}:{PORT_STH}/STH/v1/contextEntities/type/Sensor/id/urn:ngsi-ld:distance:002/attributes/distance?lastN={lastN}"
    headers = {
        'fiware-service': 'smart',  # Cabeçalhos específicos do FIWARE
        'fiware-servicepath': '/'
    }
    response = requests.get(url, headers=headers)
    
    # Verifica se a resposta foi bem-sucedida
    if response.status_code == 200:
        data = response.json()
        try:
            # Tenta extrair a lista de valores do atributo 'distance'
            values = data['contextResponses'][0]['contextElement']['attributes'][0]['values']
            return values
        except KeyError as e:
            print(f"Erro de chave: {e}")
            return []
    else:
        print(f"Erro ao acessar {url}: {response.status_code}")
        return []

# Função que converte timestamps no formato UTC para o fuso horário de Brasília
def convert_to_brasilia_time(timestamps):
    utc = pytz.utc
    brasilia = pytz.timezone('America/Sao_Paulo')
    converted = []
    for t in timestamps:
        t = t.replace('T', ' ').replace('Z', '')  # Ajusta o formato da string para datetime
        try:
            dt = datetime.strptime(t, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            dt = datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
        converted.append(utc.localize(dt).astimezone(brasilia))
    return converted

# Inicializa o app Dash
app = dash.Dash(__name__)

# Define o layout da interface do usuário
app.layout = html.Div([
    html.H1(
        'Dashboard - Monitoramento de Enchente ☔',  # Título do dashboard
        style={
            'font-family': 'Arial, sans-serif',
            'color': 'lightblue',
            'text-shadow': '1px 1px 2px black',
            'text-align': 'center',
            'margin-top': '40px',
        }
    ),
    dcc.Graph(id='graph-distance'),  # Componente do gráfico
    dcc.Store(id='data-store', data={
        'timestamps': [],  # Armazena os timestamps convertidos
        'distance': []     # Armazena os valores de distância
    }),
    dcc.Interval(
        id='interval',
        interval=5 * 1000,  # Intervalo de atualização: 5 segundos
        n_intervals=0
    )
])

# Callback que atualiza os dados armazenados a cada intervalo
@app.callback(
    Output('data-store', 'data'),       # Saída: atualiza o conteúdo do Store
    Input('interval', 'n_intervals'),   # Disparado pelo componente Interval
    State('data-store', 'data')         # Usa os dados anteriores
)
def update_data(n, stored_data):
    lastN = 30  # Número de amostras recentes a buscar
    distance_data = get_distance_data(lastN)

    if distance_data:
        # Extrai e converte os timestamps para horário de Brasília
        timestamps = [entry['recvTime'] for entry in distance_data]
        timestamps = convert_to_brasilia_time(timestamps)

        # Atualiza os dados armazenados
        stored_data['timestamps'] = timestamps
        stored_data['distance'] = [float(entry['attrValue']) for entry in distance_data]

    return stored_data

# Callback que atualiza o gráfico com base nos dados do Store
@app.callback(
    Output('graph-distance', 'figure'),
    Input('data-store', 'data')
)
def update_graph(data):
    # Se não houver dados, retorna um gráfico vazio
    if not data['timestamps'] or not data['distance']:
        return go.Figure()

    y_data = data['distance']
    mean_value = sum(y_data) / len(y_data)  # Calcula a média
    latest_value = y_data[-1]  # Valor mais recente

    fig = go.Figure()
    # Traça a curva da distância
    fig.add_trace(go.Scatter(x=data['timestamps'], y=y_data, mode='lines+markers', name='Distância', line=dict(color='orange')))
    # Traça a linha da média
    fig.add_trace(go.Scatter(x=[data['timestamps'][0], data['timestamps'][-1]],
                             y=[mean_value, mean_value], mode='lines', name='Média', line=dict(color='blue', dash='dash')))

    # Personaliza o layout do gráfico
    fig.update_layout(
        title=f'Distância Atual ({latest_value} cm)',
        xaxis_title='Tempo',
        yaxis_title='Distância (cm)',
        yaxis=dict(range=[0, max(y_data) + 10]),
        hovermode='closest'
    )

    return fig

# Roda o servidor do Dash
if __name__ == '__main__':
    app.run(debug=True, host=DASH_HOST, port=8050)
