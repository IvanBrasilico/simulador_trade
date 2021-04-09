from datetime import datetime, timedelta
from typing import Dict, Tuple


class Cotacao():
    def __init__(self, abertura, fechamento, maximo, minimo):
        self.abertura = abertura
        self.fechamento = fechamento
        self.maximo = maximo
        self.minimo = minimo

    def valor_medio(self):
        return (self.fechamento + self.abertura + self.minimo + self.maximo) / 4


class Pivot():
    """Permite calcular um Pivot e a partir dele, resistências e suporte.

    Deve ser alimentado com uma ou mais cotações anteriores. Guarda o pivot médio,
    a menor mínima e a maior máxima. Se alimentar somente com uma cotacao, dará o
    cálculo pelos dados desta. Se alimentada com uma sequência, considera tudo

    """

    def __init__(self):
        self.maximo = 0.
        self.minimo = float('inf')
        self.resistencia_2 = 0.
        self.resistencia_1 = 0.
        self.suporte_1 = 0.
        self.suporte_2 = 0.
        self.pivots = []

    def atualiza_pivot(self, cotacao: Cotacao):
        pivot = (cotacao.maximo + cotacao.minimo + cotacao.fechamento) / 3
        self.maximo = max(self.maximo, cotacao.maximo)
        self.minimo = min(self.minimo, cotacao.minimo)
        self.pivots.append(pivot)
        pivot_medio = sum(self.pivots) / len(self.pivots)
        self.resistencia_1 = (pivot_medio * 2) - self.minimo
        self.suporte_1 = (pivot_medio * 2) - self.maximo
        self.resistencia_2 = pivot_medio + self.resistencia_1 - self.suporte_1
        self.suporte_2 = pivot_medio - self.resistencia_1 - self.suporte_1


class Acao():
    def __init__(self, nome):
        self.nome = nome
        self.diadividendo = 1
        self.cotacaoatual = 0.
        self.cotacoes: Dict[datetime, Cotacao] = dict()

    def cotacao_menor_em_dias(self, data, dias, margem: 0.03):
        cotacao = self.cotacoes[data].valor_medio()
        menorcotacao = float('inf')
        for r in range(1, dias + 1):
            data = data - timedelta(days=1)
            cotacaoanterior = self.cotacoes[data].valor_medio()
            if cotacaoanterior < menorcotacao:
                menorcotacao = cotacaoanterior
        if cotacao < menorcotacao * (1 + margem):
            return True
        return False

    def tem_martelo(self, data, cabeca=0.4, cabo=2.) -> Tuple[bool, bool, float]:
        """Calcula se tem hammer normal ou invertido e retorna o sinal e intensidade.

        Como o hammer é caracterizado por uma "sombra", tem dois parâmetros:

        cabeca: tolerância da relação sombra_superior para corpo
        cabo: tolerância da relação sombra_inferior para corpo

        retuns martelo (bool), invertido(bool), intensidade(float)
        """
        cotacao_data = self.cotacoes[data]
        cotacao_anterior = self.cotacoes[data - timedelta(days=1)]
        if cotacao_anterior.fechamento < cotacao_data.abertura:  # Não é baixa
            return False, False, 0.
        corpo = abs(cotacao_data.fechamento - cotacao_data.fechamento)
        if cotacao_data.abertura > cotacao_data.fechamento:
            sombra_inferior = cotacao_data.fechamento - cotacao_data.minimo
            sombra_superior = cotacao_data.maximo - cotacao_data.abertura
        else:
            sombra_inferior = cotacao_data.abertura - cotacao_data.minimo
            sombra_superior = cotacao_data.maximo - cotacao_data.fechamento
        if sombra_superior > sombra_inferior:
            intensidade = sombra_superior / corpo
            sobra = sombra_inferior / corpo
            invertido = True
        else:
            intensidade = sombra_inferior / corpo
            sobra = sombra_superior / corpo
            invertido = False
        martelo = intensidade > cabo and sobra < cabeca
        return martelo, invertido, intensidade

    def calcula_suportedoperiodo(self, data, dias) -> Pivot:
        menorcotacao = float('inf')
        pivot = Pivot()
        for r in range(1, dias + 1):
            data = data - timedelta(days=1)
            cotacaoanterior = self.cotacoes[data].valor_medio()
            pivot.atualiza_pivot(cotacaoanterior)
        return pivot


class Trader():
    """Programar uma estratégia para simulação."""
    def __init__(self, meta=0.03, diasantes=10, diascotacoes=10):
        self.meta = meta
        self.diasantes = diasantes
        self.diascotacoes = diascotacoes
        self.acaoatual: Acao = None
        self.acaocomprada = False
        self.cotacaocompra = 0.
        self.datacompra = None

    def decide_compra(self, data: datetime):
        if self.acaocomprada:
            return False
        diasparadividendo = self.acaoatual.diadividendo - data.day
        if diasparadividendo < 0:
            diasparadividendo = 30 + diasparadividendo
        if diasparadividendo <= self.diasantes:
            if self.acaoatual.cotacao_menor_em_dias(data, self.diascotacoes):
                self.acaocomprada = True
                self.cotacaocompra = self.acaoatual.cotacoes[data].valor_medio()
                self.datacompra = data
                print(f'Comprou ação {self.acaoatual.nome} a {self.cotacaocompra}')
                return True
        return False

    def decide_venda(self, data):
        if self.acaocomprada:
            return False
        if self.cotacaocompra * (1 + self.meta) < self.acaoatual.cotacoes[data].maximo:
            print(f'Vendeu ação {self.acaoatual.nome} a {self.cotacaocompra}')
            return True
        return False
