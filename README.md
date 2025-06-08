# controleFinanceiro

Projeto em desenvolvimento para realizar um **controle financeiro completo**, com funcionalidades para gerenciar receitas, despesas (inclusive parceladas), investimentos, empréstimos e planejamentos financeiros.  
Além disso, este projeto serve como um **laboratório de estudos em Python**, Dash, Firebase, arquitetura de software e boas práticas.

---

## Objetivo do Projeto

Este repositório foi criado com **foco no aprendizado**. A ideia não é apenas entregar um sistema funcional, mas **aprender a estruturar projetos de forma segura, escalável e organizada** desde o início.

Por isso, evitei concentrar todo o código em um único arquivo (`app.py`) e segui uma estrutura modular com divisão clara de responsabilidades:

- `components/`: contém os **componentes visuais reutilizáveis** (layouts, cards, formulários, etc.).
- `services/`: camada de **comunicação com o Firebase** (leitura, escrita, atualizações de dados).
- `assets/`: arquivos estáticos como CSS, ícones, imagens, se necessário.
- `myndex.py`: arquivo principal, responsável por montar o app e controlar a navegação.
- `app.py`: centraliza a configuração global do Dash, incluindo o servidor e estilos.

> 🔐 Essa organização ajuda na **segurança**, **manutenção** e **escalabilidade** da aplicação.

---

## Funcionalidades

- [x] Cadastro e listagem de receitas e despesas
- [x] Controle de despesas parceladas
- [x] Registro de investimentos (valor aplicado, atual, retorno)
- [x] Registro de empréstimos (quem emprestou, quem recebeu, status)
- [x] Planejamento financeiro mensal/anual
- [x] Visualização com gráficos interativos (Plotly)
- [x] Interface web com responsividade usando Dash Bootstrap

---

## Tecnologias Utilizadas

Este projeto é uma oportunidade prática para estudar e aplicar:

- [Python](https://www.python.org/) – linguagem principal
- [Dash](https://dash.plotly.com/) – framework web em Python
- [Plotly](https://plotly.com/python/) – gráficos interativos
- [Pandas](https://pandas.pydata.org/) – manipulação de dados
- [Firebase Firestore](https://firebase.google.com/docs/firestore) – banco de dados em nuvem
- [Dash Bootstrap Components (DBC)](https://dash-bootstrap-components.opensource.faculty.ai/) – para criação de componentes visuais responsivos com estilo moderno (baseado no Bootstrap)

---

## Estrutura do Projeto

```plaintext
controleFinanceiro/
├── assets/                 # Arquivos estáticos (CSS, imagens)
├── components/             # Componentes visuais reutilizáveis
├── services/               # Conexões com o Firestore e outras integrações
├── firebase_config.json    # (IGNORADO no .gitignore) – configuração local do Firebase
├── app.py                  # Inicializa o Dash app com estilos e configurações globais
├── myndex.py               # Arquivo principal: monta layout, rotas, callbacks
├── .env                    # (IGNORADO) – segredos e variáveis de ambiente
├── requirements.txt        # Dependências do projeto
└── README.md

---
## Sobre a Estrutura

    - O arquivo app.py centraliza a configuração global da aplicação, como tema visual, fontes externas e inicialização do servidor.

    - O Dash app é instanciado ali com suporte ao Dash Bootstrap Components, ícones e Google Fonts.

    - O server é exportado para permitir deploy externo (ex: Heroku, Render, etc.).

    - Toda a lógica de navegação, layout e callbacks fica separada em myndex.py, o verdadeiro "cérebro" da aplicação.

Essa abordagem:

✅ Mantém o app.py limpo, reutilizável e focado em configuração.
✅ Separa responsabilidades, facilitando testes, manutenção e segurança.
✅ Prepara seu projeto para deploy profissional.

## Segurança e Boas Práticas

    - Segregação de responsabilidades: Evitar colocar tudo no app.py ajuda na legibilidade e segurança do código.

    - Não comitar segredos: arquivos sensíveis como firebase_config.json estão no .gitignore.

    - Organização em camadas: separar lógica de negócio (services), interface (components) e configuração (myndex.py) facilita testes e evolução futura.

    - Ambiente virtual: evita conflitos de dependências.

## Planos futuros

    - Autenticação de usuários

    - Integração com APIs de investimentos

    - Versão mobile mais otimizada

    - Simulador de metas financeiras

    - Adição de testes automatizados
    