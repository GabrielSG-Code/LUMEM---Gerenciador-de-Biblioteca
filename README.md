# 📚 LUMEN — Sistema de Gerenciamento de Biblioteca

> Sistema web responsivo para gerenciamento de acervo e empréstimos de livros, desenvolvido como projeto acadêmico na Universidade Salvador (UNIFACS).

---

## 📋 Sobre o Projeto

O **LUMEN** resolve problemas comuns do controle manual de bibliotecas — atrasos, falta de rastreabilidade de empréstimos e ausência de histórico organizado. O sistema atende dois perfis de usuário: **administradores** (gestão completa do acervo e usuários) e **leitores** (consulta e solicitação de empréstimos).

---

## ✨ Requisitos Funcionais

### 👤 Autenticação e Usuários
| ID | História | Perfil | Status |
|---|---|---|---|
| RF01.1 | Como usuário, quero me cadastrar com nome e e-mail para acessar a biblioteca e realizar empréstimos. | Usuário | 🔄 Sprint Backlog |
| RF01.2 | Como administrador, quero associar e alterar perfis de outros usuários para controlar acessos e permissões. | Administrador | 📋 Backlog |

### 📖 Acervo
| ID | História | Perfil | Status |
|---|---|---|---|
| RF02 | Como bibliotecário, quero cadastrar livros informando título, autor, categoria e quantidade de exemplares para manter o acervo organizado. | Bibliotecário | 🔄 Sprint Backlog |
| RF03 | Como usuário, quero buscar livros por título, autor ou categoria para encontrar rapidamente o que desejo e verificar disponibilidade. | Usuário | 📋 Backlog |
| RF05 | Controle de disponibilidade — indicar se um livro está emprestado ou disponível. | Sistema | 📋 Backlog |

### 🔁 Empréstimos e Devoluções
| ID | História | Perfil | Status |
|---|---|---|---|
| RF04.1 | Como bibliotecário, quero registrar empréstimos informando usuário, livro, data do empréstimo e data prevista de devolução. | Bibliotecário | 📋 Backlog |
| RF04.2 | Como bibliotecário, quero registrar devoluções informando usuário, livro e datas para controlar o que retornou. | Bibliotecário | 📋 Backlog |
| RF04.3 | Como leitor, quero visualizar meus empréstimos ativos para acompanhar datas de devolução e meu limite de empréstimos. | Leitor | 📋 Backlog |
| RF07 | Alertas de atraso para empréstimos com devolução em atraso. | Sistema | 📋 Backlog |

### 📊 Histórico e Relatórios
| ID | História | Perfil | Status |
|---|---|---|---|
| RF06.1 | Como leitor, quero visualizar meu histórico completo de empréstimos para acompanhar os livros que já li. | Leitor | 📋 Backlog |
| RF06.2 | Como bibliotecário, quero visualizar o histórico de empréstimos de qualquer usuário para gerenciar a situação dos leitores. | Bibliotecário | 📋 Backlog |
| RF08 | Como bibliotecário/administrador, quero gerar relatórios do acervo e empréstimos em PDF e Excel. | Adm / Bibliotecário | 📋 Backlog |

### ⚙️ Configurações
| ID | História | Perfil | Status |
|---|---|---|---|
| RF09 | Gerenciamento de parâmetros do sistema (prazos, limites de empréstimo etc.). | Administrador | 📋 Backlog |

---

## 🔒 Requisitos Não Funcionais

| ID | Requisito |
|---|---|
| RNF01 | Interface responsiva (web e mobile) |
| RNF02 | Autenticação segura com senha criptografada |
| RNF03 | Interface intuitiva e UX simples |
| RNF04 | Tempo de resposta em buscas inferior a 2 segundos |

**Legenda de status:** 📋 Backlog · 🔄 Sprint Backlog · 🛠️ Em Desenvolvimento · ✅ Concluído

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.x + Django |
| Banco de Dados | PostgreSQL |
| Frontend | HTML5 / CSS3 / JavaScript |
| Autenticação | Django Auth |
| Ambiente | virtualenv |

---

## 📁 Estrutura do Projeto

```
lumen/
├── core/                   # App principal (configurações globais)
├── books/                  # App de gerenciamento do acervo
├── loans/                  # App de empréstimos e devoluções
├── users/                  # App de gerenciamento de usuários
├── templates/              # Templates HTML globais
├── static/                 # Arquivos estáticos (CSS, JS, imagens)
├── manage.py
├── requirements.txt
├── .env.example            # Variáveis de ambiente (template)
└── README.md
```

---

## 🚀 Como Rodar Localmente

### Pré-requisitos

- Python 3.10+
- PostgreSQL 14+
- Git

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/LUMEN---Gerenciador-de-Biblioteca.git
cd LUMEN---Gerenciador-de-Biblioteca

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas credenciais do banco

# 5. Crie o banco de dados no PostgreSQL
createdb lumen_db

# 6. Execute as migrações
python manage.py migrate

# 7. Crie um superusuário
python manage.py createsuperuser

# 8. Rode o servidor
python manage.py runserver
```

Acesse em: `http://localhost:8000`

### Variáveis de Ambiente (`.env`)

```env
SECRET_KEY=sua-secret-key-aqui
DEBUG=True
DB_NAME=lumen_db
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
```

---

## 🤝 Contribuição

### Fluxo de trabalho (Git Flow simplificado)

```
main         → código estável/produção
develop      → branch de integração
feature/...  → novas funcionalidades
fix/...      → correções de bugs
```

**Nunca faça push direto na `main`.** Abra sempre um Pull Request para `develop`.

### Padrão de commits (Conventional Commits)

```
feat: adiciona busca por ISBN
fix: corrige cálculo de prazo de devolução
docs: atualiza README com instruções de setup
style: formata templates HTML
refactor: extrai lógica de empréstimo para service layer
test: adiciona testes para view de cadastro de livro
chore: atualiza dependências do requirements.txt
```

### Passo a passo para contribuir

```bash
# 1. Crie sua branch a partir de develop
git checkout develop
git checkout -b feature/nome-da-funcionalidade

# 2. Faça seus commits
git commit -m "feat: descrição clara da mudança"

# 3. Suba e abra o PR
git push origin feature/nome-da-funcionalidade
# Abra PR no GitHub: feature/... → develop
```

---

## 👥 Equipe

| Nome | GitHub |
|---|---|
| Nome do Dev 1 | [@usuario](https://github.com/usuario) |
| Nome do Dev 2 | [@usuario](https://github.com/usuario) |
| Nome do Dev 3 | [@usuario](https://github.com/usuario) |

---

## 📄 Licença

Este projeto é de uso acadêmico — Universidade Salvador (UNIFACS).
testando