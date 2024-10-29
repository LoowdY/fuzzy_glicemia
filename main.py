"""
Sistema Avançado de Controle Fuzzy para Infusão de Insulina
Com interface gráfica Tkinter e visualizações 3D
Versão atualizada e corrigida
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
import time
import threading
from PIL import Image, ImageTk
import math

class SistemaFuzzyAvancado:
    def __init__(self):
        # Definição dos universos de discurso
        self.glicemia = ctrl.Antecedent(np.arange(60, 201, 1), 'glicemia')
        self.variacao = ctrl.Antecedent(np.arange(-60, 61, 1), 'variacao')
        self.exercicio = ctrl.Antecedent(np.arange(0, 11, 1), 'exercicio')
        self.infusao = ctrl.Consequent(np.arange(0, 101, 1), 'infusao')

        self.configurar_funcoes_pertinencia()
        self.configurar_regras()

        # Histórico de dados com inicialização
        self.historico = {
            'tempo': [],
            'glicemia': [],
            'variacao': [],
            'exercicio': [],
            'infusao': []
        }

    def configurar_funcoes_pertinencia(self):
        # Glicemia
        self.glicemia['muito_baixa'] = fuzz.trapmf(self.glicemia.universe, [60, 60, 70, 80])
        self.glicemia['baixa'] = fuzz.trimf(self.glicemia.universe, [70, 85, 100])
        self.glicemia['normal'] = fuzz.trimf(self.glicemia.universe, [90, 120, 150])
        self.glicemia['alta'] = fuzz.trimf(self.glicemia.universe, [140, 170, 190])
        self.glicemia['muito_alta'] = fuzz.trapmf(self.glicemia.universe, [180, 190, 200, 200])

        # Variação
        self.variacao['queda_forte'] = fuzz.trapmf(self.variacao.universe, [-60, -60, -40, -30])
        self.variacao['queda'] = fuzz.trimf(self.variacao.universe, [-40, -20, 0])
        self.variacao['estavel'] = fuzz.trimf(self.variacao.universe, [-10, 0, 10])
        self.variacao['subida'] = fuzz.trimf(self.variacao.universe, [0, 20, 40])
        self.variacao['subida_forte'] = fuzz.trapmf(self.variacao.universe, [30, 40, 60, 60])

        # Exercício
        self.exercicio['leve'] = fuzz.trimf(self.exercicio.universe, [0, 0, 4])
        self.exercicio['moderado'] = fuzz.trimf(self.exercicio.universe, [3, 5, 7])
        self.exercicio['intenso'] = fuzz.trimf(self.exercicio.universe, [6, 10, 10])

        # Infusão
        self.infusao['muito_baixa'] = fuzz.trimf(self.infusao.universe, [0, 0, 20])
        self.infusao['baixa'] = fuzz.trimf(self.infusao.universe, [10, 30, 50])
        self.infusao['media'] = fuzz.trimf(self.infusao.universe, [40, 60, 80])
        self.infusao['alta'] = fuzz.trimf(self.infusao.universe, [70, 85, 100])
        self.infusao['muito_alta'] = fuzz.trimf(self.infusao.universe, [85, 100, 100])

    def configurar_regras(self):
        self.regras = [
            ctrl.Rule(self.glicemia['muito_baixa'] & self.variacao['queda_forte'],
                     self.infusao['muito_baixa']),
            ctrl.Rule(self.glicemia['muito_baixa'] & self.variacao['estavel'],
                     self.infusao['muito_baixa']),
            ctrl.Rule(self.glicemia['normal'] & self.variacao['estavel'] & self.exercicio['leve'],
                     self.infusao['media']),
            ctrl.Rule(self.glicemia['normal'] & self.variacao['estavel'] & self.exercicio['intenso'],
                     self.infusao['baixa']),
            ctrl.Rule(self.glicemia['alta'] & self.variacao['subida'] & self.exercicio['leve'],
                     self.infusao['alta']),
            ctrl.Rule(self.glicemia['muito_alta'] & self.variacao['subida_forte'],
                     self.infusao['muito_alta'])
        ]

        self.sistema_controle = ctrl.ControlSystem(self.regras)
        self.simulacao = ctrl.ControlSystemSimulation(self.sistema_controle)

    def calcular_saida(self, entrada):
        try:
            for key, value in entrada.items():
                self.simulacao.input[key] = value
            self.simulacao.compute()
            return {'infusao': self.simulacao.output['infusao']}
        except Exception as e:
            print(f"Erro no cálculo fuzzy: {e}")
            return {'infusao': 0.0}

class InterfaceAvancada(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Sistema Avançado de Controle Fuzzy")
        self.state('zoomed')

        # Configuração do sistema e interface
        self.sistema = SistemaFuzzyAvancado()
        self.running = True

        # Criar interface
        self.criar_interface()

        # Iniciar simulação após interface estar pronta
        self.after(100, self.iniciar_simulacao)

    def criar_interface(self):
        # Notebook para abas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        # Criar abas
        self.tab_principal = ttk.Frame(self.notebook)
        self.tab_processo = ttk.Frame(self.notebook)
        self.tab_3d = ttk.Frame(self.notebook)
        self.tab_analise = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_principal, text='Principal')
        self.notebook.add(self.tab_processo, text='Processo Fuzzy')
        self.notebook.add(self.tab_3d, text='Visualização 3D')
        self.notebook.add(self.tab_analise, text='Análise')

        # Configurar cada aba
        self.configurar_tab_principal()
        self.configurar_tab_processo()
        self.configurar_tab_3d()
        self.configurar_tab_analise()

    def configurar_tab_principal(self):
        # Frame para valores atuais
        frame_valores = ttk.LabelFrame(self.tab_principal, text="Valores Atuais")
        frame_valores.pack(fill='x', padx=5, pady=5)

        # Usar StringVar para atualização segura
        self.var_glicemia = tk.StringVar(value="Glicemia: -- mg/dL")
        self.var_variacao = tk.StringVar(value="Variação: -- mg/dL/min")
        self.var_exercicio = tk.StringVar(value="Exercício: -- /10")
        self.var_infusao = tk.StringVar(value="Infusão: -- U/h")

        # Labels usando StringVar
        ttk.Label(frame_valores, textvariable=self.var_glicemia).pack(padx=5, pady=2)
        ttk.Label(frame_valores, textvariable=self.var_variacao).pack(padx=5, pady=2)
        ttk.Label(frame_valores, textvariable=self.var_exercicio).pack(padx=5, pady=2)
        ttk.Label(frame_valores, textvariable=self.var_infusao).pack(padx=5, pady=2)

        # Frame para gráficos
        frame_graficos = ttk.Frame(self.tab_principal)
        frame_graficos.pack(fill='both', expand=True, padx=5, pady=5)

        self.fig_principal = plt.Figure(figsize=(12, 6))
        self.canvas_principal = FigureCanvasTkAgg(self.fig_principal, frame_graficos)
        self.canvas_principal.get_tk_widget().pack(fill='both', expand=True)

    def configurar_tab_processo(self):
        # Frame para fuzzificação
        frame_fuzz = ttk.LabelFrame(self.tab_processo, text="Fuzzificação")
        frame_fuzz.pack(fill='x', padx=5, pady=5)

        self.fig_fuzz = plt.Figure(figsize=(12, 8))
        self.canvas_fuzz = FigureCanvasTkAgg(self.fig_fuzz, frame_fuzz)
        self.canvas_fuzz.get_tk_widget().pack(fill='both', expand=True)

        # Frame para regras
        frame_regras = ttk.LabelFrame(self.tab_processo, text="Regras Ativas")
        frame_regras.pack(fill='x', padx=5, pady=5)

        self.text_regras = tk.Text(frame_regras, height=6)
        self.text_regras.pack(fill='x', padx=5, pady=5)

        # Frame para defuzzificação
        frame_defuzz = ttk.LabelFrame(self.tab_processo, text="Defuzzificação")
        frame_defuzz.pack(fill='both', expand=True, padx=5, pady=5)

        self.fig_defuzz = plt.Figure(figsize=(12, 4))
        self.canvas_defuzz = FigureCanvasTkAgg(self.fig_defuzz, frame_defuzz)
        self.canvas_defuzz.get_tk_widget().pack(fill='both', expand=True)

    def configurar_tab_3d(self):
        frame_controles = ttk.Frame(self.tab_3d)
        frame_controles.pack(fill='x', padx=5, pady=5)

        ttk.Label(frame_controles, text="Variáveis:").pack(side='left', padx=5)
        self.var_3d = tk.StringVar(value="glicemia_variacao")
        combo = ttk.Combobox(frame_controles, textvariable=self.var_3d)
        combo['values'] = ('glicemia_variacao', 'glicemia_exercicio', 'variacao_exercicio')
        combo.pack(side='left', padx=5)

        frame_3d = ttk.Frame(self.tab_3d)
        frame_3d.pack(fill='both', expand=True, padx=5, pady=5)

        self.fig_3d = plt.Figure(figsize=(12, 8))
        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, frame_3d)
        self.canvas_3d.get_tk_widget().pack(fill='both', expand=True)

    def configurar_tab_analise(self):
        frame_stats = ttk.LabelFrame(self.tab_analise, text="Estatísticas")
        frame_stats.pack(fill='x', padx=5, pady=5)

        self.text_stats = tk.Text(frame_stats, height=6)
        self.text_stats.pack(fill='x', padx=5, pady=5)

        frame_analise = ttk.Frame(self.tab_analise)
        frame_analise.pack(fill='both', expand=True, padx=5, pady=5)

        self.fig_analise = plt.Figure(figsize=(12, 8))
        self.canvas_analise = FigureCanvasTkAgg(self.fig_analise, frame_analise)
        self.canvas_analise.get_tk_widget().pack(fill='both', expand=True)

    def iniciar_simulacao(self):
        def simular():
            tempo = 0
            while self.running:
                try:
                    valores_entrada = {
                        'glicemia': 120 + 20 * np.sin(tempo / 50),
                        'variacao': 2 * np.cos(tempo / 50),
                        'exercicio': 5 + 3 * np.sin(tempo / 100)
                    }

                    self.after(0, lambda: self.atualizar_interface_segura(valores_entrada))

                    tempo += 1
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Erro na simulação: {e}")
                    break

        self.thread_simulacao = threading.Thread(target=simular, daemon=True)
        self.thread_simulacao.start()

    def atualizar_interface_segura(self, valores_entrada):
        try:
            # Atualizar StringVars
            self.var_glicemia.set(f"Glicemia: {valores_entrada['glicemia']:.1f} mg/dL")
            self.var_variacao.set(f"Variação: {valores_entrada['variacao']:.1f} mg/dL/min")
            self.var_exercicio.set(f"Exercício: {valores_entrada['exercicio']:.1f}/10")

            # Calcular saída
            saida = self.sistema.calcular_saida(valores_entrada)
            self.var_infusao.set(f"Infusão: {saida['infusao']:.1f} U/h")

            # Atualizar histórico
            self.atualizar_historico(valores_entrada, saida)

            # Atualizar visualizações baseado na aba atual
            aba_atual = self.notebook.select()
            if str(self.tab_processo) in str(aba_atual):
                self.atualizar_visualizacao_processo(valores_entrada)
            elif str(self.tab_3d) in str(aba_atual):
                self.atualizar_visualizacao_3d()
            elif str(self.tab_analise) in str(aba_atual):
                self.atualizar_analise(valores_entrada, saida)

            # Atualizar gráfico principal sempre
            self.atualizar_grafico_principal(valores_entrada, saida)

        except Exception as e:
            print(f"Erro na atualização da interface: {e}")

    def atualizar_historico(self, valores_entrada, saida):
        """Atualiza o histórico de dados do sistema"""
        for key in self.sistema.historico.keys():
            if key == 'tempo':
                if len(self.sistema.historico[key]) == 0:
                    self.sistema.historico[key].append(0)
                else:
                    self.sistema.historico[key].append(self.sistema.historico[key][-1] + 1)
            elif key == 'infusao':
                self.sistema.historico[key].append(saida['infusao'])
            else:
                self.sistema.historico[key].append(valores_entrada[key])

            # Manter tamanho máximo do histórico
            if len(self.sistema.historico[key]) > 100:
                self.sistema.historico[key].pop(0)

    def atualizar_grafico_principal(self, valores_entrada, saida):
        """Atualiza o gráfico principal com dados em tempo real"""
        try:
            self.fig_principal.clear()

            # Criar dois subplots
            ax1 = self.fig_principal.add_subplot(211)  # Glicemia
            ax2 = self.fig_principal.add_subplot(212)  # Infusão

            tempo = self.sistema.historico['tempo']

            # Plotar glicemia
            ax1.plot(tempo, self.sistema.historico['glicemia'], 'b-', label='Glicemia')
            ax1.axhline(y=70, color='r', linestyle='--', alpha=0.5)  # Limite inferior
            ax1.axhline(y=180, color='r', linestyle='--', alpha=0.5)  # Limite superior
            ax1.set_ylabel('Glicemia (mg/dL)')
            ax1.grid(True)
            ax1.legend()

            # Plotar infusão
            ax2.plot(tempo, self.sistema.historico['infusao'], 'g-', label='Infusão')
            ax2.set_xlabel('Tempo (s)')
            ax2.set_ylabel('Infusão (U/h)')
            ax2.grid(True)
            ax2.legend()

            self.fig_principal.tight_layout()
            self.canvas_principal.draw()

        except Exception as e:
            print(f"Erro ao atualizar gráfico principal: {e}")

    def atualizar_visualizacao_processo(self, valores_entrada):
        """Atualiza a visualização do processo fuzzy"""
        try:
            # Limpar figura de fuzzificação
            self.fig_fuzz.clear()
            gs = self.fig_fuzz.add_gridspec(3, 1)

            # Plotar funções de pertinência para cada variável
            variaveis = [
                (self.sistema.glicemia, valores_entrada['glicemia'], 'Glicemia', gs[0, 0]),
                (self.sistema.variacao, valores_entrada['variacao'], 'Variação', gs[1, 0]),
                (self.sistema.exercicio, valores_entrada['exercicio'], 'Exercício', gs[2, 0])
            ]

            for var, valor, titulo, pos in variaveis:
                ax = self.fig_fuzz.add_subplot(pos)
                self.plotar_funcoes_pertinencia(ax, var, valor, titulo)

            self.fig_fuzz.tight_layout()
            self.canvas_fuzz.draw()

            # Atualizar regras ativas
            self.atualizar_regras_ativas(valores_entrada)

            # Atualizar defuzzificação
            self.atualizar_defuzzificacao(valores_entrada)

        except Exception as e:
            print(f"Erro ao atualizar visualização do processo: {e}")

    def plotar_funcoes_pertinencia(self, ax, variavel, valor_atual, titulo):
        """Plota as funções de pertinência com valor atual"""
        for termo in variavel.terms:
            # Plotar função de pertinência
            ax.plot(variavel.universe, variavel[termo].mf, label=termo)

            # Calcular e mostrar grau de pertinência
            grau = fuzz.interp_membership(variavel.universe, variavel[termo].mf, valor_atual)
            if grau > 0:
                ax.fill_between([valor_atual, valor_atual], [0, grau],
                              color='red', alpha=0.2)
                ax.plot([valor_atual], [grau], 'ro')
                ax.text(valor_atual, grau, f'{grau:.2f}',
                       horizontalalignment='left', verticalalignment='bottom')

        # Plotar valor atual
        ax.axvline(valor_atual, color='r', linestyle='--', label=f'Valor: {valor_atual:.1f}')

        ax.set_title(titulo)
        ax.grid(True)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    def atualizar_regras_ativas(self, valores_entrada):
        """Atualiza a visualização das regras ativas"""
        self.text_regras.delete(1.0, tk.END)

        for i, regra in enumerate(self.sistema.regras):
            grau = self.calcular_ativacao_regra(regra, valores_entrada)
            if grau > 0:
                texto_regra = self.formatar_regra(regra, i+1, grau)
                self.text_regras.insert(tk.END, texto_regra + "\n")

    def atualizar_analise(self, valores_entrada, saida):
        """Atualiza as estatísticas e gráficos de análise"""
        try:
            # Atualizar estatísticas
            stats = self.calcular_estatisticas()
            self.text_stats.delete(1.0, tk.END)
            self.text_stats.insert(tk.END, stats)

            # Atualizar gráficos de análise
            self.atualizar_graficos_analise()

        except Exception as e:
            print(f"Erro ao atualizar análise: {e}")

    def destroy(self):
        """Sobrescreve método destroy para limpeza adequada"""
        self.running = False
        if hasattr(self, 'thread_simulacao'):
            self.thread_simulacao.join(timeout=1.0)
        super().destroy()

if __name__ == "__main__":
    app = InterfaceAvancada()
    app.mainloop()
