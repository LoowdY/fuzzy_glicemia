"""
Sistema de Controle Fuzzy para Infusão de Insulina
------------------------------------------------
Este sistema simula o controle de infusão de insulina baseado em lógica fuzzy.
Utiliza três variáveis de entrada (glicemia, variação da glicemia e nível de exercício)
para determinar a taxa de infusão de insulina adequada.

Autor: Claude
Data: 29/10/2024
"""

# Importação das bibliotecas necessárias
import numpy as np              # Para operações numéricas
import skfuzzy as fuzz         # Biblioteca principal de lógica fuzzy
from skfuzzy import control as ctrl  # Módulo de controle fuzzy
import pygame                   # Para a interface gráfica
from pygame.locals import *     # Constantes do Pygame
import sys                     # Para funcionalidades do sistema
import matplotlib.pyplot as plt # Para geração de gráficos
from matplotlib.backends.backend_agg import FigureCanvasAgg  # Para converter gráficos matplotlib para Pygame
import time #controle de tempo (verificaão no aplicativo)


# Inicialização do Pygame e suas fontes
pygame.init()
pygame.font.init()

# Configurações globais da janela
LARGURA, ALTURA = 1920, 1080  # Resolução Full HD
TELAS = {
    'PRINCIPAL': 0,    # Tela principal com visão geral do sistema
    'MODELAGEM': 1,    # Tela de modelagem fuzzy e funções de pertinência
    'REGRAS': 2,       # Tela com a base de regras
    'GRAFICOS': 3      # Tela com gráficos históricos
}

class SistemaFuzzy:
    """
    Classe responsável pela implementação do sistema fuzzy.
    Gerencia todas as variáveis linguísticas, funções de pertinência,
    regras e cálculos do sistema de inferência fuzzy.
    """

    def __init__(self):
        """
        Inicializa o sistema fuzzy com suas variáveis linguísticas
        e configurações básicas.
        """
        # Definição dos universos de discurso e variáveis linguísticas
        self.glicemia = ctrl.Antecedent(np.arange(60, 201, 1), 'glicemia')    # mg/dL
        self.variacao = ctrl.Antecedent(np.arange(-60, 61, 1), 'variacao')    # mg/dL/min
        self.exercicio = ctrl.Antecedent(np.arange(0, 11, 1), 'exercicio')    # Escala 0-10
        self.infusao = ctrl.Consequent(np.arange(0, 101, 1), 'infusao')       # U/h

        # Configuração inicial do sistema
        self.configurar_funcoes_pertinencia()
        self.configurar_regras()

        # Inicialização dos arrays para armazenamento do histórico
        self.historico_glicemia = []  # Armazena valores históricos de glicemia
        self.historico_insulina = []  # Armazena valores históricos de insulina
        self.historico_tempo = []     # Armazena os timestamps
        self.max_historico = 100      # Número máximo de pontos no histórico

    def configurar_funcoes_pertinencia(self):
        """
        Define todas as funções de pertinência para cada variável linguística.
        Usa funções triangulares (trimf) para simplicidade e eficiência.
        """
        # Funções de pertinência para Glicemia (mg/dL)
        self.glicemia['muito_baixa'] = fuzz.trimf(self.glicemia.universe, [60, 60, 80])
        self.glicemia['baixa'] = fuzz.trimf(self.glicemia.universe, [70, 90, 110])
        self.glicemia['normal'] = fuzz.trimf(self.glicemia.universe, [100, 130, 160])
        self.glicemia['alta'] = fuzz.trimf(self.glicemia.universe, [150, 170, 190])
        self.glicemia['muito_alta'] = fuzz.trimf(self.glicemia.universe, [180, 200, 200])

        # Funções de pertinência para Variação da Glicemia (mg/dL/min)
        self.variacao['queda_forte'] = fuzz.trimf(self.variacao.universe, [-60, -60, -30])
        self.variacao['queda'] = fuzz.trimf(self.variacao.universe, [-40, -20, 0])
        self.variacao['estavel'] = fuzz.trimf(self.variacao.universe, [-10, 0, 10])
        self.variacao['subida'] = fuzz.trimf(self.variacao.universe, [0, 20, 40])
        self.variacao['subida_forte'] = fuzz.trimf(self.variacao.universe, [30, 60, 60])

        # Funções de pertinência para Exercício (escala 0-10)
        self.exercicio['leve'] = fuzz.trimf(self.exercicio.universe, [0, 0, 4])
        self.exercicio['moderado'] = fuzz.trimf(self.exercicio.universe, [3, 5, 7])
        self.exercicio['intenso'] = fuzz.trimf(self.exercicio.universe, [6, 10, 10])

        # Funções de pertinência para Infusão de Insulina (U/h)
        self.infusao['muito_baixa'] = fuzz.trimf(self.infusao.universe, [0, 0, 20])
        self.infusao['baixa'] = fuzz.trimf(self.infusao.universe, [10, 30, 50])
        self.infusao['media'] = fuzz.trimf(self.infusao.universe, [40, 60, 80])
        self.infusao['alta'] = fuzz.trimf(self.infusao.universe, [70, 85, 100])
        self.infusao['muito_alta'] = fuzz.trimf(self.infusao.universe, [85, 100, 100])

    def configurar_regras(self):
        """
        Define a base de regras do sistema fuzzy.
        Cada regra é uma combinação de condições (antecedentes) e uma conclusão (consequente).
        """
        # Lista de regras do sistema
        self.regras = [
            # Regras para exercício leve
            ctrl.Rule(
                self.exercicio['leve'] & self.glicemia['muito_baixa'] & self.variacao['queda_forte'],
                self.infusao['muito_baixa']
            ),
            ctrl.Rule(
                self.exercicio['leve'] & self.glicemia['normal'] & self.variacao['estavel'],
                self.infusao['media']
            ),
            ctrl.Rule(
                self.exercicio['leve'] & self.glicemia['muito_alta'] & self.variacao['subida_forte'],
                self.infusao['muito_alta']
            ),

            # Regras para exercício moderado
            ctrl.Rule(
                self.exercicio['moderado'] & self.glicemia['baixa'] & self.variacao['queda'],
                self.infusao['baixa']
            ),
            ctrl.Rule(
                self.exercicio['moderado'] & self.glicemia['normal'] & self.variacao['estavel'],
                self.infusao['media']
            ),
            ctrl.Rule(
                self.exercicio['moderado'] & self.glicemia['alta'] & self.variacao['subida'],
                self.infusao['alta']
            ),

            # Regras para exercício intenso
            ctrl.Rule(
                self.exercicio['intenso'] & self.glicemia['baixa'] & self.variacao['queda'],
                self.infusao['muito_baixa']
            ),
            ctrl.Rule(
                self.exercicio['intenso'] & self.glicemia['normal'] & self.variacao['estavel'],
                self.infusao['baixa']
            ),
            ctrl.Rule(
                self.exercicio['intenso'] & self.glicemia['alta'] & self.variacao['subida'],
                self.infusao['media']
            )
        ]

        # Criação do sistema de controle com as regras definidas
        self.sistema_controle = ctrl.ControlSystem(self.regras)
        self.simulacao = ctrl.ControlSystemSimulation(self.sistema_controle)

    def calcular_saida(self, entradas):
        """
        Calcula a saída do sistema fuzzy com base nas entradas fornecidas.

        Args:
            entradas (dict): Dicionário com os valores de entrada para glicemia,
                           variação e exercício

        Returns:
            dict: Dicionário com o valor de saída (infusão de insulina)
        """
        try:
            # Atribuição dos valores de entrada
            self.simulacao.input['glicemia'] = entradas['glicemia']
            self.simulacao.input['variacao'] = entradas['variacao']
            self.simulacao.input['exercicio'] = entradas['exercicio']

            # Computação do resultado
            self.simulacao.compute()

            # Retorno do valor defuzzificado
            return {'infusao': self.simulacao.output['infusao']}
        except Exception as e:
            print(f"Erro no cálculo fuzzy: {str(e)}")
            return {'infusao': 0.0}

class InterfaceGrafica:
    """
    Classe responsável pela interface gráfica do sistema.
    Gerencia todas as visualizações e interações com o usuário.
    """

    def __init__(self):
        """Inicializa a interface gráfica e seus componentes"""
        # Configuração da janela
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Sistema Fuzzy de Controle de Insulina - Visualização Detalhada")

        # Configurações de temporização
        self.relogio = pygame.time.Clock()

        # Inicialização do sistema fuzzy
        self.sistema = SistemaFuzzy()

        # Controle de navegação
        self.tela_atual = TELAS['PRINCIPAL']

        # Definição das cores utilizadas na interface
        self.CORES = {
            'PRETO': (0, 0, 0),
            'BRANCO': (255, 255, 255),
            'AZUL': (0, 102, 204),
            'VERDE': (0, 204, 0),
            'VERMELHO': (204, 0, 0),
            'AMARELO': (255, 255, 0),
            'CINZA': (200, 200, 200),
            'AZUL_CLARO': (173, 216, 230)
        }

    def renderizar_grafico_pertinencia(self, variavel, valor_atual=None, tamanho=(400, 200)):
        """
        Renderiza um gráfico das funções de pertinência de uma variável.

        Args:
            variavel: Variável fuzzy (Antecedent ou Consequent)
            valor_atual: Valor atual da variável (opcional)
            tamanho: Tuple com dimensões do gráfico

        Returns:
            pygame.Surface: Superfície com o gráfico renderizado
        """
        # Criar figura matplotlib
        fig, ax = plt.subplots(figsize=(tamanho[0]/100, tamanho[1]/100))

        # Plotar cada função de pertinência
        for termo in variavel.terms:
            ax.plot(variavel.universe, variavel[termo].mf, label=termo)
            if valor_atual is not None:
                grau = fuzz.interp_membership(variavel.universe, variavel[termo].mf, valor_atual)
                if grau > 0:
                    ax.fill_between(variavel.universe, variavel[termo].mf, alpha=0.3)

        # Adicionar linha vertical para o valor atual
        if valor_atual is not None:
            ax.axvline(x=valor_atual, color='r', linestyle='--')

        # Configurar o gráfico
        ax.set_title(f'Funções de Pertinência - {variavel.label}')
        ax.grid(True)

        # Mover a legenda para fora do gráfico
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

        # Converter para superfície Pygame
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        renderer = canvas.get_renderer()
        raw_data = renderer.buffer_rgba()
        size = canvas.get_width_height()

        plt.close(fig)
        return pygame.image.frombuffer(raw_data, size, "RGBA")

    def desenhar_texto(self, texto, pos, cor=(255, 255, 255), tamanho=18):
        """
        Desenha texto na tela.

        Args:
            texto: Texto a ser desenhado
            pos: Posição (x, y) do texto
            cor: Cor do texto em RGB
            tamanho: Tamanho da fonte
        """
        fonte = pygame.font.SysFont("Arial", tamanho)
        superficie_texto = fonte.render(str(texto), True, cor)
        self.tela.blit(superficie_texto, pos)

    def desenhar_tela_principal(self, valores_entrada, valores_saida):
        """
        Desenha a tela principal do sistema, mostrando todas as informações relevantes
        do processo de inferência fuzzy.

        Args:
            valores_entrada (dict): Dicionário contendo os valores de entrada
                {'glicemia': float, 'variacao': float, 'exercicio': float}
            valores_saida (dict): Dicionário contendo os valores de saída
                {'infusao': float}
        """
        # Limpar a tela com cor de fundo preta
        self.tela.fill(self.CORES['PRETO'])

        # ================ SEÇÃO 1: ENTRADAS CRISP ================
        self.desenhar_texto("1. ENTRADAS CRISP", (20, 10), self.CORES['AMARELO'], 24)
        # Mostrar valores numéricos das entradas
        self.desenhar_texto(f"Glicemia: {valores_entrada['glicemia']:.1f} mg/dL", (20, 40))
        self.desenhar_texto(f"Variação: {valores_entrada['variacao']:.1f} mg/dL/min", (20, 70))
        self.desenhar_texto(f"Exercício: {valores_entrada['exercicio']:.1f}/10", (20, 100))

        # ================ SEÇÃO 2: FUZZIFICAÇÃO ================
        self.desenhar_texto("2. FUZZIFICAÇÃO", (20, 140), self.CORES['AMARELO'], 24)

        # Renderizar gráficos das funções de pertinência com valores atuais
        glicemia_surf = self.renderizar_grafico_pertinencia(
            self.sistema.glicemia,
            valores_entrada['glicemia'],
            tamanho=(500, 200)  # Tamanho aumentado para melhor visualização
        )
        variacao_surf = self.renderizar_grafico_pertinencia(
            self.sistema.variacao,
            valores_entrada['variacao'],
            tamanho=(500, 200)
        )
        exercicio_surf = self.renderizar_grafico_pertinencia(
            self.sistema.exercicio,
            valores_entrada['exercicio'],
            tamanho=(500, 200)
        )

        # Posicionar os gráficos na tela
        self.tela.blit(glicemia_surf, (20, 170))
        self.tela.blit(variacao_surf, (20, 400))
        self.tela.blit(exercicio_surf, (20, 630))

        # ================ SEÇÃO 3: REGRAS ATIVADAS ================
        self.desenhar_texto("3. REGRAS ATIVADAS", (550, 10), self.CORES['AMARELO'], 24)

        try:
            # Calcular graus de pertinência para cada regra
            y_pos = 40
            for i, regra in enumerate(self.sistema.regras):
                # Calcular grau de ativação da regra
                grau_ativacao = self.calcular_grau_ativacao_regra(regra, valores_entrada)

                # Definir cor baseada na ativação da regra
                cor = self.CORES['VERDE'] if grau_ativacao > 0 else self.CORES['BRANCO']

                # Mostrar regra e seu grau de ativação
                descricao_regra = self.formatar_regra(regra, i + 1)
                self.desenhar_texto(descricao_regra, (550, y_pos), cor)
                self.desenhar_texto(f"Ativação: {grau_ativacao:.2f}", (1200, y_pos), cor)

                y_pos += 30

            # ================ SEÇÃO 4: DEFUZZIFICAÇÃO ================
            self.desenhar_texto("4. PROCESSO DE DEFUZZIFICAÇÃO", (550, 400), self.CORES['AMARELO'], 24)

            # Renderizar gráfico de defuzzificação
            defuzz_surf = self.renderizar_defuzzificacao(
                valores_saida['infusao'],
                self.calcular_regras_ativas(valores_entrada)
            )
            self.tela.blit(defuzz_surf, (550, 430))

            # ================ SEÇÃO 5: SAÍDA CRISP ================
            self.desenhar_texto("5. SAÍDA CRISP", (550, 700), self.CORES['AMARELO'], 24)
            self.desenhar_texto(
                f"Infusão de Insulina: {valores_saida['infusao']:.1f} U/h",
                (550, 730),
                self.CORES['VERDE'],
                24
            )

        except Exception as e:
            print(f"Erro ao processar regras: {e}")

        # Atualizar a tela
        pygame.display.flip()

    def calcular_grau_ativacao_regra(self, regra, valores_entrada):
        """
        Calcula o grau de ativação de uma regra específica.

        Args:
            regra: Regra fuzzy a ser avaliada
            valores_entrada: Dicionário com os valores crisp de entrada

        Returns:
            float: Grau de ativação da regra (0 a 1)
        """
        try:
            # Obter termos e seus valores linguísticos da regra
            graus = []

            # Avaliar cada antecedente da regra
            for var_name, termo in zip(['glicemia', 'variacao', 'exercicio'], regra.antecedent_terms):
                # Obter o valor crisp da entrada
                valor = valores_entrada[var_name]

                # Calcular grau de pertinência
                if var_name == 'glicemia':
                    var = self.sistema.glicemia
                elif var_name == 'variacao':
                    var = self.sistema.variacao
                else:
                    var = self.sistema.exercicio

                grau = fuzz.interp_membership(var.universe, termo.mf, valor)
                graus.append(grau)

            # Retornar o mínimo dos graus (operador AND)
            return min(graus)

        except Exception as e:
            print(f"Erro ao calcular grau de ativação: {e}")
            return 0.0

    def formatar_regra(self, regra, num_regra):
        """
        Formata uma regra fuzzy para exibição.

        Args:
            regra: Regra fuzzy a ser formatada
            num_regra: Número da regra

        Returns:
            str: Texto formatado da regra
        """
        try:
            # Obter os antecedentes e consequentes
            antecedentes = []
            for var_name, termo in zip(['glicemia', 'variacao', 'exercicio'], regra.antecedent_terms):
                antecedentes.append(f"{var_name} é {termo.label}")

            consequente = f"infusao é {regra.consequent[0].term.label}"

            # Montar texto da regra
            return f"Regra {num_regra}: SE {' E '.join(antecedentes)} ENTÃO {consequente}"

        except Exception as e:
            print(f"Erro ao formatar regra: {e}")
            return f"Regra {num_regra}: Erro na formatação"

    def renderizar_defuzzificacao(self, valor_saida, regras_ativas):
        """
        Renderiza o gráfico do processo de defuzzificação.

        Args:
            valor_saida: Valor crisp de saída
            regras_ativas: Dicionário com as regras ativas e seus graus

        Returns:
            pygame.Surface: Superfície com o gráfico de defuzzificação
        """
        # Criar figura matplotlib
        fig, ax = plt.subplots(figsize=(8, 4))

        # Plotar funções de pertinência de saída
        x_infusao = np.linspace(0, 100, 1000)
        for termo in self.sistema.infusao.terms:
            y = fuzz.interp_membership(self.sistema.infusao.universe,
                                       self.sistema.infusao[termo].mf,
                                       x_infusao)
            ax.fill_between(x_infusao, y, alpha=0.3, label=termo)

        # Marcar valor de saída
        ax.axvline(x=valor_saida, color='r', linestyle='--', label=f'Saída: {valor_saida:.1f}')

        # Configurar gráfico
        ax.set_title('Processo de Defuzzificação')
        ax.grid(True)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

        # Converter para superfície Pygame
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        renderer = canvas.get_renderer()
        raw_data = renderer.buffer_rgba()
        size = canvas.get_width_height()

        plt.close(fig)
        return pygame.image.frombuffer(raw_data, size, "RGBA")

    def desenhar_tela_modelagem(self):
        """
        Desenha a tela de modelagem fuzzy, mostrando detalhes sobre as variáveis
        linguísticas e suas funções de pertinência.
        """
        self.tela.fill(self.CORES['PRETO'])

        # Título da tela
        self.desenhar_texto("MODELAGEM FUZZY DO SISTEMA", (20, 10), self.CORES['AMARELO'], 30)

        # Descrição das variáveis e seus intervalos
        descricoes = {
            'Glicemia (mg/dL)': {
                'universo': '[60, 200]',
                'muito_baixa': '60-80: Hipoglicemia severa',
                'baixa': '70-110: Hipoglicemia moderada',
                'normal': '100-160: Faixa ideal',
                'alta': '150-190: Hiperglicemia moderada',
                'muito_alta': '180-200: Hiperglicemia severa'
            },
            'Variação (mg/dL/min)': {
                'universo': '[-60, 60]',
                'queda_forte': '-60 a -30: Queda rápida',
                'queda': '-40 a 0: Queda moderada',
                'estavel': '-10 a 10: Estabilidade',
                'subida': '0 a 40: Aumento moderado',
                'subida_forte': '30 a 60: Aumento rápido'
            },
            'Exercício (intensidade)': {
                'universo': '[0, 10]',
                'leve': '0-4: Caminhada leve, atividades diárias',
                'moderado': '3-7: Exercícios moderados, caminhada rápida',
                'intenso': '6-10: Corrida, exercícios intensos'
            },
            'Infusão (U/h)': {
                'universo': '[0, 100]',
                'muito_baixa': '0-20: Mínima infusão',
                'baixa': '10-50: Infusão reduzida',
                'media': '40-80: Infusão moderada',
                'alta': '70-85: Infusão elevada',
                'muito_alta': '85-100: Infusão máxima'
            }
        }

        # Desenhar descrições
        y_pos = 60
        for variavel, detalhes in descricoes.items():
            # Título da variável
            self.desenhar_texto(variavel, (20, y_pos), self.CORES['VERDE'], 24)
            self.desenhar_texto(f"Universo de discurso: {detalhes['universo']}",
                                (40, y_pos + 30), self.CORES['AZUL_CLARO'])

            # Conjuntos fuzzy
            y_pos += 60
            for conjunto, descricao in detalhes.items():
                if conjunto != 'universo':
                    self.desenhar_texto(f"• {descricao}", (40, y_pos), self.CORES['BRANCO'])
                    y_pos += 25
            y_pos += 20

        # Visualização das funções de pertinência
        self.desenhar_texto("Funções de Pertinência", (600, 60), self.CORES['AMARELO'], 24)

        # Renderizar e posicionar gráficos
        variaveis = [
            (self.sistema.glicemia, "Glicemia"),
            (self.sistema.variacao, "Variação"),
            (self.sistema.exercicio, "Exercício"),
            (self.sistema.infusao, "Infusão")
        ]

        for i, (var, titulo) in enumerate(variaveis):
            surf = self.renderizar_grafico_pertinencia(var, tamanho=(500, 200))
            self.tela.blit(surf, (600, 100 + i * 220))

    def desenhar_tela_regras(self, valores_entrada):
        """
        Desenha a tela de regras do sistema, mostrando todas as regras
        e seus respectivos graus de ativação.

        Args:
            valores_entrada: Dicionário com os valores atuais das entradas
        """
        self.tela.fill(self.CORES['PRETO'])

        # Título
        self.desenhar_texto("BASE DE REGRAS DO SISTEMA", (20, 10), self.CORES['AMARELO'], 30)

        # Informações atuais
        self.desenhar_texto("Valores Atuais:", (20, 50), self.CORES['VERDE'], 24)
        self.desenhar_texto(f"Glicemia: {valores_entrada['glicemia']:.1f} mg/dL", (20, 80))
        self.desenhar_texto(f"Variação: {valores_entrada['variacao']:.1f} mg/dL/min", (20, 110))
        self.desenhar_texto(f"Exercício: {valores_entrada['exercicio']:.1f}/10", (20, 140))

        # Tabela de regras
        y_pos = 180
        self.desenhar_texto("Regras Ativas e Graus de Ativação:", (20, y_pos), self.CORES['AMARELO'], 24)
        y_pos += 40

        # Cabeçalho da tabela
        headers = ["Nº", "Antecedentes", "Consequente", "Ativação"]
        x_pos = [20, 100, 800, 1000]
        for header, x in zip(headers, x_pos):
            self.desenhar_texto(header, (x, y_pos), self.CORES['AZUL_CLARO'])
        y_pos += 30

        # Listar todas as regras
        for i, regra in enumerate(self.sistema.regras):
            # Calcular grau de ativação
            grau = self.calcular_grau_ativacao_regra(regra, valores_entrada)

            # Definir cor baseada na ativação
            cor = self.CORES['VERDE'] if grau > 0 else self.CORES['BRANCO']

            # Número da regra
            self.desenhar_texto(f"{i + 1}", (x_pos[0], y_pos), cor)

            # Antecedentes
            antecedentes = []
            for var_name, termo in zip(['glicemia', 'variacao', 'exercicio'], regra.antecedent_terms):
                antecedentes.append(f"{var_name} é {termo.label}")
            self.desenhar_texto(" E ".join(antecedentes), (x_pos[1], y_pos), cor)

            # Consequente
            consequente = f"infusao é {regra.consequent[0].term.label}"
            self.desenhar_texto(consequente, (x_pos[2], y_pos), cor)

            # Grau de ativação
            self.desenhar_texto(f"{grau:.3f}", (x_pos[3], y_pos), cor)

            y_pos += 30

    def desenhar_tela_graficos(self):
        """
        Desenha a tela de gráficos históricos do sistema.
        Mostra a evolução temporal das variáveis e análises estatísticas.
        """
        self.tela.fill(self.CORES['PRETO'])

        # Título
        self.desenhar_texto("GRÁFICOS E ANÁLISES", (20, 10), self.CORES['AMARELO'], 30)

        # Gráfico histórico de glicemia
        fig_glicemia = plt.figure(figsize=(10, 3))
        plt.plot(self.sistema.historico_tempo,
                 self.sistema.historico_glicemia,
                 'b-',
                 label='Glicemia')
        plt.title('Histórico de Glicemia')
        plt.xlabel('Tempo')
        plt.ylabel('mg/dL')
        plt.grid(True)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

        # Converter para superfície Pygame
        canvas = FigureCanvasAgg(fig_glicemia)
        canvas.draw()
        renderer = canvas.get_renderer()
        raw_data = renderer.buffer_rgba()
        size = canvas.get_width_height()
        surf_glicemia = pygame.image.frombuffer(raw_data, size, "RGBA")
        plt.close(fig_glicemia)

        # Gráfico histórico de insulina
        fig_insulina = plt.figure(figsize=(10, 3))
        plt.plot(self.sistema.historico_tempo,
                 self.sistema.historico_insulina,
                 'r-',
                 label='Insulina')
        plt.title('Histórico de Infusão de Insulina')
        plt.xlabel('Tempo')
        plt.ylabel('U/h')
        plt.grid(True)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

        # Converter para superfície Pygame
        canvas = FigureCanvasAgg(fig_insulina)
        canvas.draw()
        renderer = canvas.get_renderer()
        raw_data = renderer.buffer_rgba()
        size = canvas.get_width_height()
        surf_insulina = pygame.image.frombuffer(raw_data, size, "RGBA")
        plt.close(fig_insulina)

        # Posicionar gráficos
        self.tela.blit(surf_glicemia, (20, 60))
        self.tela.blit(surf_insulina, (20, 300))

        # Estatísticas
        if len(self.sistema.historico_glicemia) > 0:
            stats_y = 540
            self.desenhar_texto("Estatísticas:", (20, stats_y), self.CORES['AMARELO'], 24)

            glicemia_stats = {
                "Glicemia Média": np.mean(self.sistema.historico_glicemia),
                "Glicemia Máxima": np.max(self.sistema.historico_glicemia),
                "Glicemia Mínima": np.min(self.sistema.historico_glicemia),
                "Desvio Padrão": np.std(self.sistema.historico_glicemia)
            }

            insulina_stats = {
                "Insulina Média": np.mean(self.sistema.historico_insulina),
                "Insulina Máxima": np.max(self.sistema.historico_insulina),
                "Insulina Mínima": np.min(self.sistema.historico_insulina),
                "Desvio Padrão": np.std(self.sistema.historico_insulina)
            }

            stats_y += 40
            self.desenhar_texto("Glicemia:", (40, stats_y), self.CORES['AZUL_CLARO'])
            stats_y += 30
            for nome, valor in glicemia_stats.items():
                self.desenhar_texto(f"{nome}: {valor:.2f}", (60, stats_y))
                stats_y += 25

            stats_y += 20
            self.desenhar_texto("Insulina:", (40, stats_y), self.CORES['AZUL_CLARO'])
            stats_y += 30
            for nome, valor in insulina_stats.items():
                self.desenhar_texto(f"{nome}: {valor:.2f}", (60, stats_y))
                stats_y += 25

    def executar(self):
        """
        Loop principal da interface gráfica.
        Gerencia a execução do sistema, simulação dos valores e visualização.
        Implementa o controle de navegação entre telas e atualização em tempo real.
        """
        # Inicialização
        tempo = 0
        fase_glicemia = np.random.random() * 2 * np.pi
        ultima_atualizacao = time.time()
        intervalo_atualizacao = 1.0  # Atualização a cada 1 segundo

        # Menu de ajuda
        texto_ajuda = [
            "=== CONTROLES ===",
            "1 - Tela Principal",
            "2 - Modelagem Fuzzy",
            "3 - Base de Regras",
            "4 - Gráficos Históricos",
            "ESC - Sair",
            "",
            "=== INFORMAÇÕES ===",
            "Simulação em tempo real",
            "Atualização: 1 vez/s",
            "Pressione ESC para sair"
        ]

        try:
            while True:
                # Processamento de eventos
                for evento in pygame.event.get():
                    if evento.type == QUIT:
                        return
                    elif evento.type == KEYDOWN:
                        if evento.key == K_ESCAPE:
                            return
                        elif evento.key in [K_1, K_2, K_3, K_4]:
                            # Mudança de tela
                            self.tela_atual = {
                                K_1: TELAS['PRINCIPAL'],
                                K_2: TELAS['MODELAGEM'],
                                K_3: TELAS['REGRAS'],
                                K_4: TELAS['GRAFICOS']
                            }[evento.key]

                # Controle de atualização temporal
                tempo_atual = time.time()
                if tempo_atual - ultima_atualizacao >= intervalo_atualizacao:
                    # Simular novos valores
                    valores_entrada = self.simular_valores(tempo, fase_glicemia)

                    # Calcular saída do sistema fuzzy
                    try:
                        valores_saida = self.sistema.calcular_saida(valores_entrada)

                        # Atualizar histórico
                        self.atualizar_historico(tempo, valores_entrada, valores_saida)

                        # Atualizar visualização baseada na tela atual
                        self.atualizar_visualizacao(valores_entrada, valores_saida)

                    except Exception as e:
                        print(f"Erro no processamento fuzzy: {str(e)}")
                        valores_saida = {'infusao': 0.0}

                    # Atualizar tempo e última atualização
                    tempo += 1
                    ultima_atualizacao = tempo_atual

                # Desenhar menu de ajuda
                self.desenhar_menu_ajuda(texto_ajuda)

                # Atualizar tela
                pygame.display.flip()

                # Controle de FPS
                self.relogio.tick(60)

        except Exception as e:
            print(f"Erro no loop principal: {str(e)}")
        finally:
            pygame.quit()
            sys.exit()

    def simular_valores(self, tempo, fase):
        """
        Simula os valores de entrada do sistema.

        Args:
            tempo (int): Tempo atual da simulação
            fase (float): Fase para a simulação da glicemia

        Returns:
            dict: Dicionário com os valores simulados
        """
        return {
            'glicemia': self.simular_glicemia(tempo, fase),
            'variacao': self.simular_variacao(tempo, fase),
            'exercicio': self.simular_exercicio(tempo)
        }

    def simular_glicemia(self, tempo, fase):
        """
        Simula valores de glicemia usando uma função senoidal.

        Args:
            tempo (int): Tempo atual
            fase (float): Fase da função senoidal

        Returns:
            float: Valor simulado de glicemia
        """
        # Parâmetros da simulação
        base = 130  # Valor base de glicemia
        amplitude = 40  # Amplitude da variação
        periodo = 100  # Período da oscilação

        # Adicionar ruído aleatório para mais realismo
        ruido = np.random.normal(0, 2)

        return base + amplitude * np.sin(2 * np.pi * tempo / periodo + fase) + ruido

    def simular_variacao(self, tempo, fase):
        """
        Calcula a variação da glicemia entre dois instantes consecutivos.

        Args:
            tempo (int): Tempo atual
            fase (float): Fase da simulação

        Returns:
            float: Taxa de variação da glicemia
        """
        # Calcular glicemia em dois instantes consecutivos
        glicemia_atual = self.simular_glicemia(tempo, fase)
        glicemia_anterior = self.simular_glicemia(tempo - 1, fase)

        # Calcular taxa de variação
        return glicemia_atual - glicemia_anterior

    def simular_exercicio(self, tempo):
        """
        Simula a intensidade do exercício físico.

        Args:
            tempo (int): Tempo atual

        Returns:
            float: Intensidade do exercício (0-10)
        """
        # Parâmetros da simulação
        periodo_exercicio = 200
        base = 5  # Nível médio de exercício
        amplitude = 4  # Amplitude da variação

        # Adicionar ruído aleatório
        ruido = np.random.normal(0, 0.5)

        return base + amplitude * np.sin(2 * np.pi * tempo / periodo_exercicio) + ruido

    def atualizar_historico(self, tempo, valores_entrada, valores_saida):
        """
        Atualiza o histórico de valores do sistema.

        Args:
            tempo (int): Tempo atual
            valores_entrada (dict): Valores de entrada
            valores_saida (dict): Valores de saída
        """
        # Adicionar novos valores ao histórico
        self.sistema.historico_glicemia.append(valores_entrada['glicemia'])
        self.sistema.historico_insulina.append(valores_saida['infusao'])
        self.sistema.historico_tempo.append(tempo)

        # Manter tamanho máximo do histórico
        if len(self.sistema.historico_tempo) > self.sistema.max_historico:
            self.sistema.historico_glicemia.pop(0)
            self.sistema.historico_insulina.pop(0)
            self.sistema.historico_tempo.pop(0)

    def atualizar_visualizacao(self, valores_entrada, valores_saida):
        """
        Atualiza a visualização baseada na tela atual.

        Args:
            valores_entrada (dict): Valores de entrada
            valores_saida (dict): Valores de saída
        """
        self.tela.fill(self.CORES['PRETO'])

        if self.tela_atual == TELAS['PRINCIPAL']:
            self.desenhar_tela_principal(valores_entrada, valores_saida)
        elif self.tela_atual == TELAS['MODELAGEM']:
            self.desenhar_tela_modelagem()
        elif self.tela_atual == TELAS['REGRAS']:
            self.desenhar_tela_regras(valores_entrada)
        elif self.tela_atual == TELAS['GRAFICOS']:
            self.desenhar_tela_graficos()

    def desenhar_menu_ajuda(self, texto_ajuda):
        """
        Desenha o menu de ajuda na tela.

        Args:
            texto_ajuda (list): Lista de strings com o texto de ajuda
        """
        for i, linha in enumerate(texto_ajuda):
            self.desenhar_texto(
                linha,
                (LARGURA - 200, 20 + i * 25),
                self.CORES['CINZA'],
                16
            )

if __name__ == "__main__":
    # Criar e executar a interface
    interface = InterfaceGrafica()

