 Barbearia Juandev

Sistema web desenvolvido para uma barbearia, com foco em agendamento de horários, gerenciamento de serviços e administração da agenda.

O projeto foi desenvolvido como prática durante meus estudos em Engenharia de Software, utilizando Python e Flask no back-end, SQLite para persistência dos dados e HTML, CSS e JavaScript no front-end.

 Funcionalidades

Área do cliente

- Visualização dos serviços disponíveis
- Visualização dos planos mensais
- Consulta de horários disponíveis
- Agendamento de horários
- Informações da barbearia

 Painel administrativo

- Login de administrador
- Dashboard administrativo
- Gerenciamento de horários
- Criação e exclusão de horários
- Gerenciamento de serviços
- Criação, edição e exclusão de serviços
- Gerenciamento de planos
- Criação, edição e exclusão de planos
- Visualização dos agendamentos
- Cancelamento de agendamentos

 Tecnologias utilizadas

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript

🗄️ Banco de dados

O sistema utiliza SQLite para armazenar:

- Horários
- Agendamentos
- Serviços
- Planos mensais

O banco é inicializado automaticamente pela aplicação.

ESTRUTURA DO PROJETO

```text
barbearia-juandev/
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   ├── admin/
│   │   ├── agendamentos.html
│   │   ├── base_admin.html
│   │   ├── dashboard.html
│   │   ├── horarios.html
│   │   ├── planos.html
│   │   └── servicos.html
│   ├── base.html
│   └── index.html
├── app.py
├── db.py
├── requirements.txt
└── .gitignore
