# Sistema Fuzzy de Controle de Insulina

## Descrição
O sistema implementa um controlador fuzzy para administração de insulina, levando em consideração múltiplas variáveis de entrada para determinar a taxa ideal de infusão de insulina. O sistema possui uma interface gráfica interativa que permite o monitoramento em tempo real e análise detalhada do processo de controle.

### Principais Características

- **Múltiplas Variáveis de Entrada:**
  - Glicemia (40-400 mg/dL)
  - Taxa de variação da glicemia (-20 a +20 mg/dL/min)
  - Nível de exercício (0-10)
  - Nível de estresse (0-10)
  - Ingestão de carboidratos (0-150g)

- **Interface Gráfica Avançada:**
  - Monitoramento em tempo real
  - Visualização do processo de fuzzificação
  - Acompanhamento das regras ativas
  - Visualização do processo de defuzzificação
  - Análise estatística detalhada

- **Sistema de Regras Fuzzy:**
  - Regras adaptativas baseadas em múltiplos fatores
  - Consideração de situações críticas (hipoglicemia/hiperglicemia)
  - Ajuste dinâmico baseado em exercício e estresse

- **Análise e Estatísticas:**
  - Tempo no alvo glicêmico
  - Distribuição de glicemia
  - Correlação entre variáveis
  - Histórico detalhado

## Requisitos Técnicos

### Dependências
```
numpy
skfuzzy
tkinter
matplotlib
```

### Bibliotecas Principais
- `numpy`: Processamento numérico
- `skfuzzy`: Implementação da lógica fuzzy
- `tkinter`: Interface gráfica
- `matplotlib`: Visualização de dados

## Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITÓRIO]
```

2. Instale as dependências:
```bash
pip install numpy scikit-fuzzy matplotlib
```

3. Execute o programa:
```bash
python main.py
```

## Estrutura do Sistema

### Classes Principais

1. **SistemaFuzzyInsulina**
   - Implementa a lógica fuzzy
   - Gerencia as regras e inferências
   - Mantém o histórico do sistema

2. **InterfaceGrafica**
   - Implementa a interface do usuário
   - Gerencia as visualizações
   - Coordena a atualização em tempo real

### Módulos

- **Configuração do Sistema Fuzzy:**
  - Definição de universos de discurso
  - Configuração de funções de pertinência
  - Implementação de regras de inferência

- **Monitoramento:**
  - Visualização em tempo real
  - Gráficos de tendência
  - Indicadores de desempenho

- **Análise:**
  - Estatísticas de controle
  - Distribuições
  - Correlações entre variáveis

## Funcionalidades

### Monitoramento em Tempo Real
- Acompanhamento da glicemia atual
- Visualização da taxa de infusão de insulina
- Indicadores de estado do paciente

### Análise Fuzzy
- Visualização das funções de pertinência
- Acompanhamento das regras ativas
- Processo de defuzzificação

### Análise Estatística
- Tempo no alvo glicêmico
- Distribuição de valores
- Tendências e correlações

## Uso do Sistema

1. **Inicialização:**
   - Execute o programa
   - O sistema iniciará automaticamente a simulação

2. **Monitoramento:**
   - Observe os valores em tempo real na aba "Monitor"
   - Acompanhe as tendências nos gráficos

3. **Análise:**
   - Utilize as diferentes abas para análises específicas
   - Examine as estatísticas na aba "Análise"

## Logs e Depuração
- O sistema mantém logs detalhados em `controle_insulina.log`
- Informações de debug e erro são registradas
- Facilita a identificação e resolução de problemas

---

### Informações do Projeto

**Sistema Fuzzy de Controle de Insulina**

**Autor**  
João Renan S. Lopes

**Orientação**  
Profa. Polyana Nascimento

**Turma**  
CC6NA

**Sobre o Projeto**  
Este projeto foi desenvolvido como parte da disciplina de Inteligência Artificial, demonstrando a aplicação prática de lógica fuzzy no controle de insulina para pacientes com diabetes.
