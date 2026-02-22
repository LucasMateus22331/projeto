# 📦 Sistema de Controle de Estoque e Produção

> Um sistema desenvolvido em Python para gerenciar o fluxo de estoque, desde a entrada de peças individuais até a montagem e saída do produto final.

---

## Sobre o Projeto

estou trabalgando pra desenvolver melhor e facilitar o acesso, só para administradores

Este projeto é uma aplicação desktop (GUI) que visa facilitar o controle de inventário de uma linha de montagem. O diferencial deste sistema é a **lógica de produção**: ele não apenas cadastra itens, mas entende a relação entre "Peças" e "Produto Final".

O sistema conecta-se a um banco de dados para garantir que todas as informações sejam salvas de forma segura e persistente, banco de dados feito em python.

### ⚙️ Lógica do Sistema
O fluxo principal funciona da seguinte maneira:

1.  **Entrada de Peças:** O usuário cadastra as peças que chegaram (ex: Sensores, Carcaças, Cabos).
2.  **Montagem (Produção):** Ao solicitar a criação de um produto final (ex: "Mouse Gamer"), o sistema verifica se há peças suficientes.
3.  **Atualização Automática:** Se houver peças, o sistema:
    * ➖ **Subtrai** as peças necessárias do estoque de componentes.
    * ➕ **Adiciona** o produto pronto ao estoque de venda.
    * 💾 **Salva** tudo no banco de dados instantaneamente.

---

## 🚀 Funcionalidades

- [x] **Login de Administrador:** Acesso seguro ao sistema.
- [x] **Cadastro de Peças:** Adicionar novas matérias-primas ao estoque.
- [x] **Controle de Produção:** Botão para "Montar Produto" que dá baixa automática nos componentes.
- [x] **Dashboard:** Visualização rápida da quantidade de peças e produtos prontos.
- [x] **Banco de Dados:** Conexão com MySQL para persistência dos dados.
- [ ] **Relatórios:** (Em breve) Exportação de movimentações em PDF/Excel.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3
* **Interface Gráfica (GUI):** Tkinter / CustomTkinter
* **Banco de Dados:** MySQL (ou SQLite)
* **Driver DB:** mysql-connector-python

obs: projeito feito para treinar e academico



