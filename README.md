# 🛠️ Sistema de Gestão de Vida Útil de Ferramentas CNC

Aplicação web desenvolvida para monitoramento em tempo real, controle de desgaste e gestão de setups de ferramentas em centros de usinagem CNC. O sistema tem como foco a integridade dos dados operacionais e o fornecimento de métricas precisas para a engenharia de processos e análise de *tool life*.

---

## 📌 Funcionalidades Principais

* **Gestão de Magazine CNC (T1 a T20):** Cadastro e controle estrito de posições do magazine, respeitando os limites operacionais das máquinas.
* **Cadastro de Produtos e Receitas de Setup:** Associação flexível (*n:n*) entre produtos e as ferramentas necessárias em sua linha de produção.
* **Apontamento de Produção com Recálculo Automático:** Sincronização dinâmica da vida útil consumida a partir dos lotes produzidos.
* **Análise de Durabilidade sem Teto Artificial (Over-limit):** Acúmulo real do desgaste permitindo ultrapassar 100% da vida nominal para estudos de engenharia de corte, com indicação visual de alerta em vermelho.
* **Rastreabilidade e Histórico de Trocas:** Registro completo de substituições de ferramentas contendo operador, data, hora e motivo técnico.

---

## 🚀 Tecnologias Utilizadas

* **Linguagem:** Python 3.x
* **Framework Web:** Flask (Arquitetura modular com *Blueprints*)
* **Banco de Dados:** SQLite3 (Modelagem relacional com execução de *queries* agregadas)
* **Front-end:** HTML5, CSS3, JavaScript e Bootstrap 5

---

## 🧠 Diferenciais Técnicos e Regras de Negócio

| Regra / Módulo | Descrição Técnica |
| :--- | :--- |
| **Sincronização por `SUM`** | Elimina erros de contagem acumulada. Toda alteração, edição ou exclusão de apontamento dispara uma recampagem direta via somatório relacional na base de dados. |
| **Estudo de *Tool Life*** | O sistema não trava a contagem ao atingir 100% do limite configurado, garantindo dados reais para a engenharia avaliar o desgaste severo antes da quebra. |
| **Validação Rigorosa** | Restrição de entrada de dados na interface administrativa para impedir o cadastro de posições inválidas fora do intervalo `T1-T20`. |

---

## 🗄️ Estrutura do Banco de Dados

* `ferramentas`: Armazena a posição (`posicao`), nome, limite de vida útil (`vida_util_limite`) e peças produzidas acumuladas (`pecas_produzidas`).
* `produtos`: Registra o código identificador e a descrição dos produtos.
* `produto_ferramentas`: Tabela pivô que vincula cada produto às posições de ferramentas utilizadas no seu setup.
* `historico_apontamentos`: Registro do volume de peças usinadas, ordem de produção e data.
* `historico_trocas`: Log auditável de substituição das ferramentas e seus respectivos motivos.

---

## 📂 Estrutura do Projeto

```text
├── app.py                      # Ponto de entrada da aplicação
├── database.py                 # Conexão e inicialização do banco SQLite
├── admin.py                    # Blueprint contendo as rotas e regras do painel
├── database.db                 # Arquivo do banco de dados SQLite
├── templates/                  # Arquivos HTML (Jinja2)
│   ├── admin.html              # Dashboard principal
│   ├── login.html              # Autenticação
│   ├── editar_apontamento.html # Edição de registros
│   ├── editar_ferramenta.html  # Alteração de parâmetros
│   └── editar_produto.html     # Alteração de setup de produtos
└── static/                     # Arquivos estáticos (CSS, JS, Imagens)
```

---

## 🔧 Como Executar o Projeto

**1. Clonar o repositório:**
```bash
git clone https://github.com/WellFl/GestaoFerramentas_SoftwareProduct.git
cd GestaoFerramentas_SoftwareProduct
```

**2. Criar e ativar o ambiente virtual:**
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate

**3. Instalar as dependências:**
pip install flask

**4. Iniciar a aplicação:**
python app.py

**5. Acessar no navegador:**
http://127.0.0.1:5000

---

## 👤 Autor
Wellison Santos Lima Ferreira

Graduando em Análise e Desenvolvimento de Sistemas (Faculdade Impacta de Tecnologia)