import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
from queue import Queue
import logging
from datetime import datetime

# Configuração do sistema de logging
logging.basicConfig(
    level=logging.DEBUG,  # Alterado para DEBUG para mais detalhes
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('controle_insulina.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SistemaFuzzyInsulina:
    """
    Implementa o sistema fuzzy para controle de insulina com múltiplas
    variáveis de entrada e conjunto abrangente de regras.
    """
    def __init__(self):
        """
        Inicializa o sistema fuzzy, definindo universos de discurso,
        funções de pertinência e regras de inferência.
        """
        self.configurar_universos()
        self.configurar_funcoes_pertinencia()
        self.configurar_regras()
        self.configurar_sistema_controle()

        # Inicialização do histórico com pré-alocação
        self.tamanho_max_historico = 1000
        self.historico = {
            'timestamp': np.zeros(self.tamanho_max_historico),
            'glicemia': np.zeros(self.tamanho_max_historico),
            'taxa_variacao': np.zeros(self.tamanho_max_historico),
            'exercicio': np.zeros(self.tamanho_max_historico),
            'estresse': np.zeros(self.tamanho_max_historico),
            'carboidratos': np.zeros(self.tamanho_max_historico),
            'insulina': np.zeros(self.tamanho_max_historico)
        }
        self.indice_historico = 0
        self.tempo_inicio = time.time()

    def configurar_universos(self):
        """
        Define os universos de discurso para todas as variáveis do sistema.
        Cada universo é configurado com um range apropriado para a variável.
        """
        # Glicemia em mg/dL (40 a 400)
        self.glicemia = ctrl.Antecedent(np.linspace(40, 400, 361), 'glicemia')

        # Taxa de variação da glicemia em mg/dL/min (-20 a +20)
        self.taxa_variacao = ctrl.Antecedent(np.linspace(-20, 20, 41), 'taxa_variacao')

        # Nível de exercício (0 a 10)
        self.exercicio = ctrl.Antecedent(np.linspace(0, 10, 11), 'exercicio')

        # Nível de estresse (0 a 10)
        self.estresse = ctrl.Antecedent(np.linspace(0, 10, 11), 'estresse')

        # Ingestão de carboidratos em gramas (0 a 150)
        self.carboidratos = ctrl.Antecedent(np.linspace(0, 150, 151), 'carboidratos')

        # Taxa de infusão de insulina em U/h (0 a 25)
        self.insulina = ctrl.Consequent(np.linspace(0, 25, 251), 'insulina')

    def configurar_funcoes_pertinencia(self):
        """
        Define as funções de pertinência para cada variável linguística
        do sistema, utilizando formas trapezoidais e triangulares.
        """
        # Funções de pertinência para Glicemia
        self.glicemia['hipoglicemia'] = fuzz.trapmf(self.glicemia.universe, [40, 40, 65, 75])
        self.glicemia['normal_baixa'] = fuzz.trimf(self.glicemia.universe, [70, 85, 100])
        self.glicemia['normal'] = fuzz.trimf(self.glicemia.universe, [90, 110, 130])
        self.glicemia['normal_alta'] = fuzz.trimf(self.glicemia.universe, [120, 140, 160])
        self.glicemia['hiperglicemia'] = fuzz.trapmf(self.glicemia.universe, [150, 180, 400, 400])

        # Funções de pertinência para Taxa de Variação
        self.taxa_variacao['caindo_rapido'] = fuzz.trapmf(self.taxa_variacao.universe, [-20, -20, -4, -2])
        self.taxa_variacao['caindo'] = fuzz.trimf(self.taxa_variacao.universe, [-3, -1.5, 0])
        self.taxa_variacao['estavel'] = fuzz.trimf(self.taxa_variacao.universe, [-1, 0, 1])
        self.taxa_variacao['subindo'] = fuzz.trimf(self.taxa_variacao.universe, [0, 1.5, 3])
        self.taxa_variacao['subindo_rapido'] = fuzz.trapmf(self.taxa_variacao.universe, [2, 4, 20, 20])

        # Funções de pertinência para Exercício
        self.exercicio['nenhum'] = fuzz.trimf(self.exercicio.universe, [0, 0, 3])
        self.exercicio['leve'] = fuzz.trimf(self.exercicio.universe, [2, 4, 6])
        self.exercicio['moderado'] = fuzz.trimf(self.exercicio.universe, [5, 7, 9])
        self.exercicio['intenso'] = fuzz.trimf(self.exercicio.universe, [8, 10, 10])

        # Funções de pertinência para Estresse
        self.estresse['baixo'] = fuzz.trimf(self.estresse.universe, [0, 0, 4])
        self.estresse['medio'] = fuzz.trimf(self.estresse.universe, [3, 5, 7])
        self.estresse['alto'] = fuzz.trimf(self.estresse.universe, [6, 10, 10])

        # Funções de pertinência para Carboidratos
        self.carboidratos['jejum'] = fuzz.trimf(self.carboidratos.universe, [0, 0, 20])
        self.carboidratos['pouco'] = fuzz.trimf(self.carboidratos.universe, [15, 30, 45])
        self.carboidratos['medio'] = fuzz.trimf(self.carboidratos.universe, [40, 60, 80])
        self.carboidratos['muito'] = fuzz.trimf(self.carboidratos.universe, [75, 150, 150])

        # Funções de pertinência para Insulina
        self.insulina['zero'] = fuzz.trimf(self.insulina.universe, [0, 0, 1])
        self.insulina['baixa'] = fuzz.trimf(self.insulina.universe, [0.5, 2, 4])
        self.insulina['media'] = fuzz.trimf(self.insulina.universe, [3, 6, 9])
        self.insulina['alta'] = fuzz.trimf(self.insulina.universe, [8, 12, 16])
        self.insulina['muito_alta'] = fuzz.trimf(self.insulina.universe, [15, 25, 25])

    def configurar_regras(self):
        """
        Define o conjunto de regras fuzzy que governam o sistema.
        """
        self.regras = []

        # Regras para hipoglicemia
        self.regras.extend([
            ('R1', ctrl.Rule(
                antecedent=self.glicemia['hipoglicemia'],
                consequent=self.insulina['zero'],
                label='Hipoglicemia - Parar insulina'
            )),
            ('R2', ctrl.Rule(
                antecedent=(self.glicemia['hipoglicemia'] &
                           self.taxa_variacao['caindo_rapido']),
                consequent=self.insulina['zero'],
                label='Hipoglicemia em queda rápida - Parar insulina'
            )),
        ])

        # Regras para glicemia normal
        self.regras.extend([
            ('R3', ctrl.Rule(
                antecedent=(self.glicemia['normal'] &
                           self.taxa_variacao['estavel'] &
                           self.exercicio['nenhum'] &
                           self.carboidratos['jejum']),
                consequent=self.insulina['baixa'],
                label='Glicemia normal estável em jejum - Insulina basal'
            )),
            ('R4', ctrl.Rule(
                antecedent=(self.glicemia['normal'] &
                           self.carboidratos['medio']),
                consequent=self.insulina['media'],
                label='Glicemia normal com refeição média - Insulina moderada'
            )),
        ])

        # Regras para hiperglicemia
        self.regras.extend([
            ('R5', ctrl.Rule(
                antecedent=self.glicemia['hiperglicemia'],
                consequent=self.insulina['alta'],
                label='Hiperglicemia - Aumentar insulina'
            )),
            ('R6', ctrl.Rule(
                antecedent=(self.glicemia['hiperglicemia'] &
                           self.taxa_variacao['subindo_rapido']),
                consequent=self.insulina['muito_alta'],
                label='Hiperglicemia em ascensão rápida - Insulina máxima'
            )),
        ])

        # Regras para exercício
        self.regras.extend([
            ('R7', ctrl.Rule(
                antecedent=self.exercicio['intenso'],
                consequent=self.insulina['baixa'],
                label='Exercício intenso - Reduzir insulina'
            )),
            ('R8', ctrl.Rule(
                antecedent=(self.exercicio['moderado'] &
                           self.glicemia['normal']),
                consequent=self.insulina['baixa'],
                label='Exercício moderado com glicemia normal - Insulina reduzida'
            )),
        ])

        # Regras para estresse
        self.regras.extend([
            ('R9', ctrl.Rule(
                antecedent=(self.estresse['alto'] &
                           self.glicemia['normal_alta']),
                consequent=self.insulina['alta'],
                label='Estresse alto com glicemia elevada - Aumentar insulina'
            )),
        ])

        # Regras para alimentação
        self.regras.extend([
            ('R10', ctrl.Rule(
                antecedent=(self.carboidratos['muito'] &
                           self.glicemia['normal']),
                consequent=self.insulina['alta'],
                label='Refeição rica em carboidratos - Aumentar insulina'
            )),
        ])

        logger.info(f"Sistema configurado com {len(self.regras)} regras de inferência")

    def configurar_sistema_controle(self):
        """
        Configura o sistema de controle fuzzy com as regras definidas
        e prepara o simulador para execução.
        """
        # Criar sistema de controle com todas as regras
        self.sistema_controle = ctrl.ControlSystem([regra[1] for regra in self.regras])
        # Criar simulador
        self.simulador = ctrl.ControlSystemSimulation(self.sistema_controle)

        logger.info("Sistema de controle e simulador configurados com sucesso")

    def get_var_term_from_antecedent(self, antecedent):
        """
        Mapeia um objeto antecedente para sua variável e termo correspondente.

        Args:
            antecedent: Objeto antecedente a ser mapeado.

        Returns:
            tuple: (nome_variavel, termo) ou (None, None) se não encontrado.
        """
        for var in [self.glicemia, self.taxa_variacao, self.exercicio, self.estresse, self.carboidratos]:
            for termo in var.terms:
                if antecedent is var[termo]:
                    logger.debug(f"Mapeado antecedente {antecedent} para variável '{var.label}' e termo '{termo}'")
                    return var.label, termo
        logger.debug(f"Antecedente {antecedent} não mapeado para nenhuma variável e termo conhecidos")
        return None, None

    def calcular_saida(self, entradas):
        """
        Calcula a saída do sistema fuzzy com base nas entradas fornecidas.

        Args:
            entradas (dict): Dicionário com valores para cada variável de entrada

        Returns:
            dict: Dicionário com resultados do processo fuzzy
        """
        try:
            # Atualizar entradas no simulador
            for var, valor in entradas.items():
                self.simulador.input[var] = valor

            # Computar resultado
            self.simulador.compute()

            # Obter saída crisp
            saida_crisp = self.simulador.output['insulina']

            # Calcular graus de pertinência das entradas
            pertinencias_entrada = self.calcular_pertinencias_entrada(entradas)

            # Calcular ativação das regras
            ativacao_regras = self.calcular_ativacao_regras(pertinencias_entrada)

            # Calcular pertinências de saída
            pertinencias_saida = self.calcular_pertinencias_saida(saida_crisp)

            # Registrar no log
            logger.info(f"Saída calculada: {saida_crisp:.2f} U/h")

            # Registrar ativação das regras no log
            for nome_regra, info in ativacao_regras.items():
                logger.info(f"Regra {nome_regra} ativada com grau {info['grau']:.3f}")

            return {
                'crisp': saida_crisp,
                'pertinencias_entrada': pertinencias_entrada,
                'ativacao_regras': ativacao_regras,
                'pertinencias_saida': pertinencias_saida
            }

        except Exception as e:
            logger.error(f"Erro no cálculo fuzzy: {str(e)}")
            return None

    def calcular_pertinencias_entrada(self, entradas):
        """
        Calcula os graus de pertinência para todas as entradas.

        Args:
            entradas (dict): Valores das variáveis de entrada

        Returns:
            dict: Graus de pertinência para cada termo linguístico
        """
        pertinencias = {}

        # Para cada variável de entrada
        for var_name, valor in entradas.items():
            pertinencias[var_name] = {}
            variavel = getattr(self, var_name)

            # Para cada termo linguístico da variável
            for termo in variavel.terms:
                funcao_pert = variavel[termo].mf
                grau = fuzz.interp_membership(
                    variavel.universe, funcao_pert, valor)
                pertinencias[var_name][termo] = grau
                logger.debug(f"Pertinência de '{var_name}' termo '{termo}': {grau:.3f}")

        return pertinencias

    def calcular_ativacao_regras(self, pertinencias_entrada):
        """
        Calcula o grau de ativação de cada regra do sistema.
        Isso é feito avaliando os antecedentes de cada regra com base nas pertinências das entradas.

        Args:
            pertinencias_entrada (dict): Graus de pertinência das entradas

        Returns:
            dict: Grau de ativação de cada regra
        """
        ativacoes = {}

        for nome_regra, regra in self.regras:
            try:
                # Extrair antecedentes da regra
                antecedentes = regra.antecedent

                # Verificar se a regra possui múltiplos antecedentes
                termos = []
                def extrair_termos(antecedente):
                    if isinstance(antecedente, ctrl.Antecedent):
                        termos.append(antecedente)
                    elif hasattr(antecedente, 'children'):
                        for child in antecedente.children:
                            extrair_termos(child)

                extrair_termos(antecedentes)

                # Calcular o grau de ativação (mínimo para AND)
                graus = []
                for termo_obj in termos:
                    var_name, termo = self.get_var_term_from_antecedent(termo_obj)
                    if var_name and termo:
                        grau = pertinencias_entrada[var_name][termo]
                        graus.append(grau)
                    else:
                        logger.error(f"Termo não mapeado corretamente para a regra {nome_regra}")
                        graus.append(0.0)

                grau_ativacao = np.min(graus) if graus else 0.0

                ativacoes[nome_regra] = {
                    'grau': grau_ativacao,
                    'label': regra.label
                }

                logger.debug(f"Regra {nome_regra} ativada com grau {grau_ativacao:.3f}")

            except Exception as e:
                logger.error(f"Erro ao avaliar regra {nome_regra}: {str(e)}")
                ativacoes[nome_regra] = {
                    'grau': 0.0,
                    'label': f"Erro na avaliação da regra {nome_regra}"
                }

        return ativacoes

    def calcular_pertinencias_saida(self, valor_crisp):
        """
        Calcula os graus de pertinência da saída para o valor crisp calculado.

        Args:
            valor_crisp (float): Valor defuzzificado da saída

        Returns:
            dict: Graus de pertinência para cada termo da variável de saída
        """
        pertinencias = {}

        # Para cada termo linguístico da variável de saída
        for termo in self.insulina.terms:
            funcao_pert = self.insulina[termo].mf
            grau = fuzz.interp_membership(
                self.insulina.universe, funcao_pert, valor_crisp)
            pertinencias[termo] = grau
            logger.debug(f"Pertinência de saída termo '{termo}': {grau:.3f}")

        return pertinencias

    def atualizar_historico(self, entradas, saida):
        """
        Atualiza o histórico do sistema com novos valores.

        Args:
            entradas (dict): Valores das variáveis de entrada
            saida (float): Valor da saída (insulina)
        """
        idx = self.indice_historico % self.tamanho_max_historico

        # Registrar timestamp
        self.historico['timestamp'][idx] = time.time() - self.tempo_inicio

        # Registrar valores de entrada
        for var_name, valor in entradas.items():
            self.historico[var_name][idx] = valor

        # Registrar saída
        self.historico['insulina'][idx] = saida

        self.indice_historico += 1

    def obter_historico_atual(self):
        """
        Retorna o histórico atual do sistema.

        Returns:
            dict: Histórico do sistema com os dados coletados até o momento
        """
        idx = self.indice_historico if self.indice_historico < self.tamanho_max_historico else self.tamanho_max_historico
        historico_atual = {key: self.historico[key][:idx] for key in self.historico}
        return historico_atual

class InterfaceGrafica(tk.Tk):
    """
    Interface gráfica principal do sistema com múltiplas abas de visualização.
    Permite monitoramento em tempo real e análise detalhada do processo fuzzy.
    """
    def __init__(self):
        super().__init__()

        self.title("Sistema Fuzzy de Controle de Insulina")
        self.state('zoomed')  # Maximizar janela

        # Configurar sistema fuzzy
        self.sistema = SistemaFuzzyInsulina()

        # Configurar fila de atualização
        self.fila_atualizacao = Queue()
        self.executando = True

        # Configurar interface
        self.criar_interface()

        # Iniciar simulação
        self.iniciar_simulacao()

        logger.info("Interface gráfica iniciada com sucesso")

    def criar_interface(self):
        """
        Cria a interface gráfica com todas as abas e elementos necessários.
        """
        # Configurar estilo
        estilo = ttk.Style()
        estilo.configure('TNotebook.Tab', padding=[12, 6])

        # Notebook principal
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        # Criar abas
        self.abas = {
            'Monitor': self.criar_aba_monitor(),
            'Fuzzificação': self.criar_aba_fuzzificacao(),
            'Regras': self.criar_aba_regras(),
            'Defuzzificação': self.criar_aba_defuzzificacao(),
            'Análise': self.criar_aba_analise()
        }

        # Adicionar abas ao notebook
        for nome, frame in self.abas.items():
            self.notebook.add(frame, text=nome)

        # Configurar atualização ao mudar de aba
        self.notebook.bind('<<NotebookTabChanged>>', self.ao_mudar_aba)

    def criar_aba_monitor(self):
        """
        Cria a aba de monitoramento em tempo real.

        Returns:
            ttk.Frame: Frame contendo os elementos da aba
        """
        aba = ttk.Frame(self.notebook)

        # Frame para valores atuais
        frame_valores = ttk.LabelFrame(aba, text="Valores Atuais")
        frame_valores.pack(fill='x', padx=5, pady=5)

        # Variáveis de exibição
        self.vars_display = {
            'glicemia': tk.StringVar(value="Glicemia: --- mg/dL"),
            'taxa_variacao': tk.StringVar(value="Variação: --- mg/dL/min"),
            'exercicio': tk.StringVar(value="Exercício: --- /10"),
            'estresse': tk.StringVar(value="Estresse: --- /10"),
            'carboidratos': tk.StringVar(value="Carboidratos: --- g"),
            'insulina': tk.StringVar(value="Insulina: --- U/h")
        }

        # Criar labels com fonte maior
        for var_name, var in self.vars_display.items():
            label = ttk.Label(
                frame_valores,
                textvariable=var,
                font=('Arial', 12, 'bold')
            )
            label.pack(padx=5, pady=2)

        # Frame para gráficos
        frame_graficos = ttk.Frame(aba)
        frame_graficos.pack(fill='both', expand=True, padx=5, pady=5)

        # Criar gráficos
        self.fig_monitor = plt.Figure(figsize=(14, 8), dpi=100)
        self.ax_glicemia = self.fig_monitor.add_subplot(211)
        self.ax_insulina = self.fig_monitor.add_subplot(212)

        self.canvas_monitor = FigureCanvasTkAgg(self.fig_monitor, frame_graficos)
        self.canvas_monitor.get_tk_widget().pack(fill='both', expand=True)

        # Configurar gráficos
        self.configurar_graficos_monitor()

        return aba

    def configurar_graficos_monitor(self):
        """
        Configura a aparência inicial dos gráficos de monitoramento.
        """
        # Gráfico de glicemia
        self.ax_glicemia.set_ylabel('Glicemia (mg/dL)', fontsize=10)
        self.ax_glicemia.set_title('Monitoramento da Glicemia', fontsize=14, pad=15)
        self.ax_glicemia.grid(True, linestyle='--', alpha=0.7)
        self.ax_glicemia.axhspan(70, 180, color='green', alpha=0.1, label='Faixa Alvo')

        # Gráfico de insulina
        self.ax_insulina.set_xlabel('Tempo (min)', fontsize=10)
        self.ax_insulina.set_ylabel('Taxa de Infusão (U/h)', fontsize=10)
        self.ax_insulina.set_title('Taxa de Infusão de Insulina', fontsize=14, pad=15)
        self.ax_insulina.grid(True, linestyle='--', alpha=0.7)

        # Ajustar layout
        self.fig_monitor.tight_layout()

    def criar_aba_fuzzificacao(self):
        """
        Cria a aba de visualização do processo de fuzzificação.

        Returns:
            ttk.Frame: Frame contendo os elementos da aba
        """
        aba = ttk.Frame(self.notebook)

        # Frame para funções de pertinência
        frame_funpert = ttk.LabelFrame(aba, text="Funções de Pertinência")
        frame_funpert.pack(fill='both', expand=True, padx=5, pady=5)

        # Criar gráficos
        self.fig_fuzz = plt.Figure(figsize=(14, 10), dpi=100)
        self.canvas_fuzz = FigureCanvasTkAgg(self.fig_fuzz, frame_funpert)
        self.canvas_fuzz.get_tk_widget().pack(fill='both', expand=True)

        return aba

    def criar_aba_regras(self):
        """
        Cria a aba de visualização das regras ativas.

        Returns:
            ttk.Frame: Frame contendo os elementos da aba
        """
        aba = ttk.Frame(self.notebook)

        # Frame para regras
        frame_regras = ttk.LabelFrame(aba, text="Regras Ativas")
        frame_regras.pack(fill='both', expand=True, padx=5, pady=5)

        # Criar Treeview para regras
        colunas = ('Regra', 'Descrição', 'Ativação')
        self.tree_regras = ttk.Treeview(frame_regras, columns=colunas, show='headings')

        # Configurar colunas
        for col in colunas:
            self.tree_regras.heading(col, text=col)
            self.tree_regras.column(col, width=150, anchor='center')

        self.tree_regras.column('Descrição', width=500, anchor='w')
        self.tree_regras.pack(fill='both', expand=True, padx=5, pady=5)

        # Adicionar scrollbar
        scrollbar = ttk.Scrollbar(frame_regras, orient='vertical', command=self.tree_regras.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree_regras['yscrollcommand'] = scrollbar.set

        return aba

    def criar_aba_defuzzificacao(self):
        """
        Cria a aba de visualização do processo de defuzzificação.

        Returns:
            ttk.Frame: Frame contendo os elementos da aba
        """
        aba = ttk.Frame(self.notebook)

        # Frame para gráfico
        frame_defuzz = ttk.LabelFrame(aba, text="Processo de Defuzzificação")
        frame_defuzz.pack(fill='both', expand=True, padx=5, pady=5)

        self.fig_defuzz = plt.Figure(figsize=(14, 6), dpi=100)
        self.ax_defuzz = self.fig_defuzz.add_subplot(111)
        self.canvas_defuzz = FigureCanvasTkAgg(self.fig_defuzz, frame_defuzz)
        self.canvas_defuzz.get_tk_widget().pack(fill='both', expand=True)

        return aba

    def criar_aba_analise(self):
        """
        Cria a aba de análise estatística.

        Returns:
            ttk.Frame: Frame contendo os elementos da aba
        """
        aba = ttk.Frame(self.notebook)

        # Frame para estatísticas
        frame_stats = ttk.LabelFrame(aba, text="Análise Estatística")
        frame_stats.pack(fill='x', padx=5, pady=5)

        self.text_stats = tk.Text(
            frame_stats,
            height=10,
            font=('Arial', 11),
            wrap='word',
            state=tk.DISABLED
        )
        self.text_stats.pack(fill='x', padx=5, pady=5)

        # Frame para gráficos
        frame_graficos = ttk.Frame(aba)
        frame_graficos.pack(fill='both', expand=True, padx=5, pady=5)

        self.fig_analise = plt.Figure(figsize=(14, 8), dpi=100)
        self.canvas_analise = FigureCanvasTkAgg(self.fig_analise, frame_graficos)
        self.canvas_analise.get_tk_widget().pack(fill='both', expand=True)

        return aba

    def iniciar_simulacao(self):
        """
        Inicia a simulação em uma thread separada.
        """
        def simular():
            tempo = 0
            while self.executando:
                try:
                    # Simular valores de entrada com variações realistas
                    entradas = {
                        'glicemia': 100 + 50 * np.sin(tempo/50) + np.random.normal(0, 5),
                        'taxa_variacao': 5 * np.cos(tempo/50) + np.random.normal(0, 1),
                        'exercicio': 5 + 4 * np.sin(tempo/100) + np.random.normal(0, 0.5),
                        'estresse': 5 + 3 * np.cos(tempo/75) + np.random.normal(0, 0.5),
                        'carboidratos': 50 + 30 * np.sin(tempo/200) + np.random.normal(0, 5)
                    }

                    # Garantir limites
                    entradas['glicemia'] = np.clip(entradas['glicemia'], 40, 400)
                    entradas['taxa_variacao'] = np.clip(entradas['taxa_variacao'], -20, 20)
                    entradas['exercicio'] = np.clip(entradas['exercicio'], 0, 10)
                    entradas['estresse'] = np.clip(entradas['estresse'], 0, 10)
                    entradas['carboidratos'] = np.clip(entradas['carboidratos'], 0, 150)

                    # Colocar na fila
                    self.fila_atualizacao.put(entradas)

                    # Atualizar interface
                    self.after(0, self.processar_atualizacao)

                    tempo += 1
                    time.sleep(0.1)  # 100ms de intervalo

                except Exception as e:
                    logger.error(f"Erro na simulação: {str(e)}")

        self.thread_simulacao = threading.Thread(target=simular, daemon=True)
        self.thread_simulacao.start()

        logger.info("Simulação iniciada")

    def processar_atualizacao(self):
        """
        Processa as atualizações pendentes na fila e atualiza a interface.
        """
        try:
            while not self.fila_atualizacao.empty():
                # Obter próxima entrada da fila
                entradas = self.fila_atualizacao.get_nowait()

                # Calcular saída do sistema fuzzy
                resultado = self.sistema.calcular_saida(entradas)
                if resultado is None:
                    continue

                # Atualizar histórico
                self.sistema.atualizar_historico(entradas, resultado['crisp'])

                # Atualizar interface baseado na aba atual
                self.atualizar_interface(entradas, resultado)

        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}")

    def atualizar_interface(self, entradas, resultado):
        """
        Atualiza todos os elementos da interface com novos dados.

        Args:
            entradas (dict): Valores atuais das variáveis de entrada
            resultado (dict): Resultado do processamento fuzzy
        """
        # Atualizar valores exibidos
        self.vars_display['glicemia'].set(f"Glicemia: {entradas['glicemia']:.1f} mg/dL")
        self.vars_display['taxa_variacao'].set(f"Variação: {entradas['taxa_variacao']:.1f} mg/dL/min")
        self.vars_display['exercicio'].set(f"Exercício: {entradas['exercicio']:.1f}/10")
        self.vars_display['estresse'].set(f"Estresse: {entradas['estresse']:.1f}/10")
        self.vars_display['carboidratos'].set(f"Carboidratos: {entradas['carboidratos']:.1f} g")
        self.vars_display['insulina'].set(f"Insulina: {resultado['crisp']:.2f} U/h")

        # Identificar aba atual
        aba_atual = self.notebook.tab(self.notebook.select(), "text")

        # Atualizar visualizações específicas da aba
        if aba_atual == "Monitor":
            self.atualizar_monitor()
        elif aba_atual == "Fuzzificação":
            self.atualizar_fuzzificacao(entradas, resultado['pertinencias_entrada'])
        elif aba_atual == "Regras":
            self.atualizar_regras(resultado['ativacao_regras'])
        elif aba_atual == "Defuzzificação":
            self.atualizar_defuzzificacao(resultado)
        elif aba_atual == "Análise":
            self.atualizar_analise()

    def atualizar_monitor(self):
        """
        Atualiza os gráficos da aba de monitoramento com melhor visualização.
        """
        # Obter histórico
        historico = self.sistema.obter_historico_atual()

        # Limpar gráficos
        self.ax_glicemia.cla()
        self.ax_insulina.cla()

        # Plotar glicemia
        self.ax_glicemia.plot(historico['timestamp']/60, historico['glicemia'],
                             'b-', label='Glicemia', linewidth=2)

        # Configurar faixa alvo de glicemia
        self.ax_glicemia.fill_between(historico['timestamp']/60, 70, 180,
                                     color='green', alpha=0.1, label='Faixa Alvo (70-180 mg/dL)')

        # Configurações do gráfico de glicemia
        self.ax_glicemia.set_ylabel('Glicemia (mg/dL)', fontsize=10)
        self.ax_glicemia.set_title('Monitoramento da Glicemia', fontsize=14, pad=15)
        self.ax_glicemia.grid(True, linestyle='--', alpha=0.7)
        self.ax_glicemia.legend(loc='upper right', fontsize=9)
        self.ax_glicemia.set_ylim(40, 400)  # Limites fixos para melhor visualização

        # Plotar insulina
        self.ax_insulina.plot(historico['timestamp']/60, historico['insulina'],
                             'g-', label='Insulina', linewidth=2)

        # Configurações do gráfico de insulina
        self.ax_insulina.set_xlabel('Tempo (min)', fontsize=10)
        self.ax_insulina.set_ylabel('Taxa de Infusão (U/h)', fontsize=10)
        self.ax_insulina.set_title('Taxa de Infusão de Insulina', fontsize=14, pad=15)
        self.ax_insulina.grid(True, linestyle='--', alpha=0.7)
        self.ax_insulina.legend(loc='upper right', fontsize=9)
        self.ax_insulina.set_ylim(0, 25)  # Limites fixos para melhor visualização

        # Ajustar layout
        self.fig_monitor.tight_layout()
        self.canvas_monitor.draw()

    def atualizar_fuzzificacao(self, entradas, pertinencias):
        """
        Atualiza os gráficos de fuzzificação.

        Args:
            entradas (dict): Valores atuais das variáveis
            pertinencias (dict): Graus de pertinência calculados
        """
        # Limpar figura
        self.fig_fuzz.clear()

        # Configurar subplots
        variaveis = [
            (self.sistema.glicemia, 'glicemia', 'Glicemia (mg/dL)'),
            (self.sistema.taxa_variacao, 'taxa_variacao', 'Taxa de Variação (mg/dL/min)'),
            (self.sistema.exercicio, 'exercicio', 'Nível de Exercício'),
            (self.sistema.estresse, 'estresse', 'Nível de Estresse'),
            (self.sistema.carboidratos, 'carboidratos', 'Carboidratos (g)')
        ]

        # Criar grid de subplots
        gs = self.fig_fuzz.add_gridspec(len(variaveis), 1, hspace=0.6)

        # Plotar cada variável
        for idx, (var, nome, titulo) in enumerate(variaveis):
            ax = self.fig_fuzz.add_subplot(gs[idx, 0])
            self.plotar_funcao_pertinencia(
                ax, var, entradas[nome],
                pertinencias[nome], titulo
            )

        self.fig_fuzz.tight_layout()
        self.canvas_fuzz.draw()

    def plotar_funcao_pertinencia(self, ax, variavel, valor_atual, pertinencias, titulo):
        """
        Plota as funções de pertinência de uma variável.

        Args:
            ax: Axes do matplotlib
            variavel: Variável fuzzy
            valor_atual: Valor atual da variável
            pertinencias: Graus de pertinência
            titulo: Título do gráfico
        """
        # Gerar cores para os termos
        cores = plt.cm.Set3(np.linspace(0, 1, len(variavel.terms)))

        # Plotar cada função de pertinência
        for termo, cor in zip(variavel.terms, cores):
            y = variavel[termo].mf
            ax.plot(variavel.universe, y, label=termo, color=cor, linewidth=2)

            # Mostrar grau de pertinência
            grau = pertinencias[termo]
            if grau > 0.01:  # Mostrar apenas graus significativos
                ax.fill_between(
                    [valor_atual, valor_atual],
                    [0, grau],
                    color=cor,
                    alpha=0.3
                )
                ax.plot([valor_atual], [grau], 'o', color=cor)
                ax.text(
                    valor_atual + 2,
                    grau,
                    f'{grau:.2f}',
                    verticalalignment='bottom',
                    fontsize=8
                )

        # Plotar linha do valor atual
        ax.axvline(
            valor_atual,
            color='red',
            linestyle='--',
            label=f'Valor Atual: {valor_atual:.1f}'
        )

        # Configurações do gráfico
        ax.set_title(titulo, fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', fontsize='small')

    def atualizar_regras(self, ativacoes):
        """
        Atualiza a visualização das regras ativas.

        Args:
            ativacoes (dict): Dicionário com graus de ativação das regras
        """
        # Limpar tabela
        for item in self.tree_regras.get_children():
            self.tree_regras.delete(item)

        # Adicionar regras ordenadas por grau de ativação
        for nome_regra, info in sorted(
            ativacoes.items(),
            key=lambda x: x[1]['grau'],
            reverse=True
        ):
            # Definir cor baseada no grau de ativação
            grau = info['grau']
            tag = 'ativa' if grau > 0.1 else 'inativa'

            # Inserir na tabela
            self.tree_regras.insert(
                '',
                'end',
                values=(
                    nome_regra,
                    info['label'],
                    f"{grau:.3f}"
                ),
                tags=(tag,)
            )

        # Configurar cores
        self.tree_regras.tag_configure('ativa', foreground='green')
        self.tree_regras.tag_configure('inativa', foreground='gray')

    def atualizar_defuzzificacao(self, resultado):
        """
        Atualiza o gráfico de defuzzificação.

        Args:
            resultado (dict): Resultado do processamento fuzzy
        """
        # Limpar gráfico
        self.ax_defuzz.cla()

        # Plotar funções de pertinência de saída
        x = self.sistema.insulina.universe
        cores = plt.cm.Set3(np.linspace(0, 1, len(self.sistema.insulina.terms)))

        for termo, cor in zip(self.sistema.insulina.terms, cores):
            y = self.sistema.insulina[termo].mf
            grau = resultado['pertinencias_saida'][termo]

            # Plotar função de pertinência
            self.ax_defuzz.plot(x, y, color=cor, linewidth=2,
                              label=f"{termo} ({grau:.2f})")

            # Plotar área ativada
            if grau > 0.01:
                y_ativado = np.minimum(grau, y)
                self.ax_defuzz.fill_between(x, 0, y_ativado,
                                          color=cor, alpha=0.3)

        # Plotar valor defuzzificado
        self.ax_defuzz.axvline(
            resultado['crisp'],
            color='red',
            linestyle='--',
            label=f"Saída: {resultado['crisp']:.2f} U/h"
        )

        # Configurações do gráfico
        self.ax_defuzz.set_title('Processo de Defuzzificação', fontsize=14, pad=15)
        self.ax_defuzz.set_xlabel('Taxa de Infusão de Insulina (U/h)', fontsize=10)
        self.ax_defuzz.set_ylabel('Grau de Pertinência', fontsize=10)
        self.ax_defuzz.grid(True, linestyle='--', alpha=0.7)
        self.ax_defuzz.legend(loc='upper right', fontsize=9)

        self.fig_defuzz.tight_layout()
        self.canvas_defuzz.draw()

    def atualizar_analise(self):
        """
        Atualiza as estatísticas e gráficos de análise com visualização melhorada.
        """
        # Obter histórico
        historico = self.sistema.obter_historico_atual()

        # Atualizar estatísticas com formatação melhorada
        self.text_stats.config(state=tk.NORMAL)
        self.text_stats.delete(1.0, tk.END)

        stats = "ANÁLISE ESTATÍSTICA DO CONTROLE GLICÊMICO\n"
        stats += "=" * 50 + "\n\n"

        # Análise da Glicemia
        glicemia = historico['glicemia']
        if len(glicemia) > 0:
            # Cálculo do tempo no alvo
            tempo_total = len(glicemia)
            tempo_alvo = np.sum((glicemia >= 70) & (glicemia <= 180))
            tempo_hipo = np.sum(glicemia < 70)
            tempo_hiper = np.sum(glicemia > 180)

            stats += "GLICEMIA:\n"
            stats += f"• Média: {np.mean(glicemia):.1f} mg/dL\n"
            stats += f"• Desvio Padrão: {np.std(glicemia):.1f} mg/dL\n"
            stats += f"• Mínimo: {np.min(glicemia):.1f} mg/dL\n"
            stats += f"• Máximo: {np.max(glicemia):.1f} mg/dL\n"
            stats += f"• Tempo no Alvo (70-180 mg/dL): {(tempo_alvo/tempo_total)*100:.1f}%\n"
            stats += f"• Tempo em Hipoglicemia: {(tempo_hipo/tempo_total)*100:.1f}%\n"
            stats += f"• Tempo em Hiperglicemia: {(tempo_hiper/tempo_total)*100:.1f}%\n\n"

        # Análise da Insulina
        insulina = historico['insulina']
        if len(insulina) > 0:
            stats += "INSULINA:\n"
            stats += f"• Taxa Média: {np.mean(insulina):.2f} U/h\n"
            stats += f"• Taxa Máxima: {np.max(insulina):.2f} U/h\n"
            stats += f"• Insulina Total: {np.sum(insulina)/60:.2f} U\n\n"  # Convertendo para unidades totais

        self.text_stats.insert(tk.END, stats)
        self.text_stats.config(state=tk.DISABLED)

        # Atualizar gráficos
        self.atualizar_graficos_analise(historico)

    def atualizar_graficos_analise(self, historico):
        """
        Atualiza os gráficos de análise com visualização melhorada.
        """
        # Limpar figura
        self.fig_analise.clear()

        # Configurar grid de subplots
        gs = self.fig_analise.add_gridspec(2, 2, hspace=0.4, wspace=0.3)

        # 1. Gráfico de séries temporais
        ax1 = self.fig_analise.add_subplot(gs[0, :])
        tempo_min = historico['timestamp']/60

        # Plotar glicemia
        line_glicemia = ax1.plot(tempo_min, historico['glicemia'],
                                'b-', label='Glicemia', linewidth=2)[0]
        ax1.set_ylabel('Glicemia (mg/dL)', color='b', fontsize=10)
        ax1.tick_params(axis='y', labelcolor='b')

        # Adicionar faixa alvo
        ax1.fill_between(tempo_min, 70, 180, color='green', alpha=0.1,
                        label='Faixa Alvo (70-180 mg/dL)')

        # Plotar insulina (escala secundária)
        ax2 = ax1.twinx()
        line_insulina = ax2.plot(tempo_min, historico['insulina'],
                                'g-', label='Insulina', linewidth=2)[0]
        ax2.set_ylabel('Taxa de Infusão (U/h)', color='g', fontsize=10)
        ax2.tick_params(axis='y', labelcolor='g')

        # Configurações do gráfico
        ax1.set_title('Monitoramento Temporal', fontsize=16, pad=20)
        ax1.set_xlabel('Tempo (min)', fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)

        # Combinar legendas
        lines = [line_glicemia, line_insulina]
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper right', fontsize=10)

        # 2. Histograma de glicemia
        ax3 = self.fig_analise.add_subplot(gs[1, 0])
        ax3.hist(historico['glicemia'], bins=30, color='blue', alpha=0.6,
                 density=True, label='Distribuição')
        ax3.axvline(70, color='r', linestyle='--', label='Limite Inferior')
        ax3.axvline(180, color='r', linestyle='--', label='Limite Superior')

        # Configurações do histograma
        ax3.set_title('Distribuição da Glicemia', fontsize=14)
        ax3.set_xlabel('Glicemia (mg/dL)', fontsize=12)
        ax3.set_ylabel('Densidade', fontsize=12)
        ax3.grid(True, linestyle='--', alpha=0.7)
        ax3.legend(fontsize=10)

        # 3. Gráfico de dispersão
        ax4 = self.fig_analise.add_subplot(gs[1, 1])
        ax4.scatter(historico['glicemia'], historico['insulina'],
                    alpha=0.5, c='green', label='Correlação')

        # Adicionar linha de tendência
        if len(historico['glicemia']) > 1:
            z = np.polyfit(historico['glicemia'], historico['insulina'], 1)
            p = np.poly1d(z)
            ax4.plot(historico['glicemia'], p(historico['glicemia']),
                    'r--', alpha=0.8, label='Tendência')

        # Configurações do gráfico de dispersão
        ax4.set_title('Correlação Glicemia x Insulina', fontsize=14)
        ax4.set_xlabel('Glicemia (mg/dL)', fontsize=12)
        ax4.set_ylabel('Taxa de Infusão (U/h)', fontsize=12)
        ax4.grid(True, linestyle='--', alpha=0.7)
        ax4.legend(fontsize=10)

        # Ajustar layout
        self.fig_analise.tight_layout()
        self.canvas_analise.draw()

    def ao_mudar_aba(self, event):
        """
        Callback executado quando o usuário muda de aba.
        Garante que a visualização atual seja atualizada.

        Args:
            event: Evento de mudança de aba
        """
        # Obtém última entrada e resultado
        historico = self.sistema.obter_historico_atual()
        if self.sistema.indice_historico == 0:
            return

        # Reconstroi última entrada
        ultima_entrada = {
            'glicemia': historico['glicemia'][-1],
            'taxa_variacao': historico['taxa_variacao'][-1],
            'exercicio': historico['exercicio'][-1],
            'estresse': historico['estresse'][-1],
            'carboidratos': historico['carboidratos'][-1]
        }

        # Recalcula resultado
        resultado = self.sistema.calcular_saida(ultima_entrada)
        if resultado:
            self.atualizar_interface(ultima_entrada, resultado)

    def finalizar(self):
        """
        Finaliza a aplicação de forma segura,
        encerrando threads e liberando recursos.
        """
        try:
            # Parar simulação
            self.executando = False

            # Aguardar thread de simulação
            if hasattr(self, 'thread_simulacao'):
                self.thread_simulacao.join(timeout=1.0)

            # Salvar log final
            logger.info("Aplicação finalizada normalmente")

            # Destruir janela
            self.destroy()

        except Exception as e:
            logger.error(f"Erro ao finalizar aplicação: {str(e)}")
            self.destroy()

def main():
    """
    Função principal que inicializa e executa a aplicação.
    """
    try:
        # Configurar logger
        logger.info("Iniciando Sistema de Controle de Insulina")

        # Criar e executar aplicação
        app = InterfaceGrafica()
        app.protocol("WM_DELETE_WINDOW", app.finalizar)
        app.mainloop()

    except Exception as e:
        logger.error(f"Erro fatal na aplicação: {str(e)}")
        messagebox.showerror(
            "Erro Fatal",
            f"Um erro fatal ocorreu:\n{str(e)}\n\nConsulte o log para mais detalhes."
        )

if __name__ == "__main__":
    main()
