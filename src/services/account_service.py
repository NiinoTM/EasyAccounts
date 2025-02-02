from src.database.connection import Database
from src.core.accounts import AccountManager
from src.utils.validators import validate_account_type
from src.utils.validators import normalizar_nome
from src.utils.search_utils import select_from_list  # Import the function
from typing import List, Optional
from src.database.models import AccountCategory
from src.utils.backup import create_backup
import sqlite3

class AccountService:
    def __init__(self):
        self.db = Database()
        self.db.connect()
        self.account_manager = AccountManager(self.db)

    def cadastros_menu(self):
        while True:
            print("\n=== Menu de Cadastros ===")
            print("1. Tipos de Conta")
            print("2. Categorias")
            print("3. Contas")
            print("4. Voltar")
            
            try:
                opcao = int(input("\nEscolha uma opção: "))
                if opcao == 1:
                    self.menu_tipos_conta()
                elif opcao == 2:
                    self.menu_categorias()
                elif opcao == 3:
                    self.menu_contas()
                elif opcao == 4:
                    break
                else:
                    print("Opção inválida!")
            except ValueError:
                print("Por favor, digite um número válido!")

    
    def menu_categorias(self):
        while True:
            print("\n=== Gerenciar Categorias ===")
            print("1. Cadastrar Categoria")
            print("2. Visualizar Categorias")
            print("3. Atualizar Categoria")
            print("4. Excluir Categoria")
            print("5. Voltar")
            
            try:
                opcao = int(input("\nEscolha uma opção: "))
                if opcao == 1:
                    self.cadastrar_categoria()
                elif opcao == 2:
                    self.visualizar_categorias()
                elif opcao == 3:
                    self.atualizar_categoria()
                elif opcao == 4:
                    self.excluir_categoria()
                elif opcao == 5:
                    break
                else:
                    print("Opção inválida!")
            except ValueError:
                print("Por favor, digite um número válido!")

    def menu_contas(self):
        while True:
            print("\n=== Gerenciar Contas ===")
            print("1. Cadastrar Conta")
            print("2. Visualizar Contas")
            print("3. Atualizar Conta")
            print("4. Excluir Conta")
            print("5. Voltar")
            
            try:
                opcao = int(input("\nEscolha uma opção: "))
                if opcao == 1:
                    self.cadastrar_conta()
                elif opcao == 2:
                    self.visualizar_contas()
                elif opcao == 3:
                    self.atualizar_conta()
                elif opcao == 4:
                    self.excluir_conta()
                elif opcao == 5:
                    break
                else:
                    print("Opção inválida!")
            except ValueError:
                print("Por favor, digite um número válido!")

    def cadastrar_categoria(self):
        print("\n--- Cadastrar Categoria ---")
        nome = input("Nome da categoria: ").strip()  # Mantém o nome original
        if nome == "":
            raise ValueError("Nome não pode estar em branco")
        nome_normalizado = normalizar_nome(nome)  # Normaliza o nome
        descricao = input("Descrição (opcional): ")

        # Verificar se o nome normalizado já existe
        sql_check = "SELECT id FROM account_categories WHERE normalized_name = ?"
        result = self.db.execute(sql_check, (nome_normalizado,)).fetchone()
        if result:
            print("Erro: Já existe uma categoria com esse nome (ou um nome semelhante).")
            return

        # Inserir a categoria no banco de dados
        sql = """
        INSERT INTO account_categories (name, normalized_name, description)
        VALUES (?, ?, ?)
        """
        self.db.execute(sql, (nome, nome_normalizado, descricao))
        create_backup()
        print("Categoria cadastrada com sucesso!")

    def visualizar_categorias(self):
        print("\n--- Categorias Cadastradas ---")
        sql = "SELECT id, name, description FROM account_categories"
        categorias = self.db.execute(sql).fetchall()

        if not categorias:
            print("Nenhuma categoria cadastrada.")
            return None

        for cat in categorias:
            print(f"ID: {cat[0]}")
            print(f"Nome: {cat[1]}")
            print(f"Descrição: {cat[2] or 'Não informada'}")
            print("-" * 30)
        
        return categorias

    def get_categories_by_name_or_id(self, search_term: str) -> List[AccountCategory]:
        """
        Retrieves categories that match the search term (ID or name).
        If search_term is empty, returns all categories.
        """
        sql = """
        SELECT id, name, description 
        FROM account_categories 
        WHERE id = ? OR name LIKE ?
        """
        try:
            # Try to convert the search term to an integer (for ID search)
            category_id = int(search_term)
            results = self.db.execute(sql, (category_id, f"%{search_term}%")).fetchall()
        except ValueError:
            # If search term is not a number, search only by name
            if search_term.strip():  # If search_term is not empty
                results = self.db.execute(sql, (-1, f"%{search_term}%")).fetchall()
            else:
                # If search_term is empty, return all categories
                sql_all = "SELECT id, name, description FROM account_categories"
                results = self.db.execute(sql_all).fetchall()

        return [AccountCategory(*result) for result in results]

    def atualizar_categoria(self):
        print("\n--- Atualizar Categoria ---")
        
        # Obtém a lista de categorias
        categorias = self.get_categories_by_name_or_id("")
        if not categorias:
            print("Nenhuma categoria cadastrada.")
            return
        
        # Seleciona a categoria usando a função select_from_list
        categoria_selecionada = select_from_list(categorias, "Selecione a categoria que deseja atualizar", key='name')
        if not categoria_selecionada:
            return
        
        # Solicita os novos dados da categoria
        novo_nome = input("Novo nome da categoria: ").strip()
        if novo_nome == "":
            raise ValueError("Nome não pode estar em branco")
        nova_desc = input("Nova descrição (opcional): ").strip()
        
        # Atualiza a categoria no banco de dados
        sql = "UPDATE account_categories SET name = ?, description = ? WHERE id = ?"
        self.db.execute(sql, (novo_nome, nova_desc, categoria_selecionada.id))
        create_backup()
        print("Categoria atualizada com sucesso!")

    def excluir_categoria(self):
        print("\n--- Excluir Categoria ---")
        
        # Obtém a lista de categorias
        categorias = self.get_categories_by_name_or_id("")
        if not categorias:
            print("Nenhuma categoria cadastrada.")
            return
        
        # Seleciona a categoria usando a função select_from_list
        categoria_selecionada = select_from_list(categorias, "Selecione a categoria que deseja atualizar", key='name')
        if not categoria_selecionada:
            return
        
        # Confirma a exclusão
        confirma = input("Tem certeza que deseja excluir esta categoria? (s/n): ").lower()
        if confirma == 's':
            sql = "DELETE FROM account_categories WHERE id = ?"
            self.db.execute(sql, (categoria_selecionada.id,))
            create_backup()
            print("Categoria excluída com sucesso!")
        else:
            print("Operação cancelada.")

    def cadastrar_conta(self):
        print("\n--- Cadastrar Conta ---")

        nome = input("Nome da conta: ").strip()  # Mantém o nome original

        if nome == "":
            raise ValueError('Nome não pode estar em branco')

        nome_normalizado = normalizar_nome(nome)  # Normaliza o nome

        # Verificar se o nome normalizado já existe
        sql_check = "SELECT id FROM accounts WHERE normalized_name = ?"
        result = self.db.execute(sql_check, (nome_normalizado,)).fetchone()
        if result:
            print("Erro: Já existe uma conta com esse nome (ou um nome semelhante).")
            return

        # Escolher entre débito ou crédito
        print("\nEscolha o tipo de conta:")
        print("1. Débito")
        print("2. Crédito")
        try:
            tipo_opcao = int(input("Escolha uma opção (1 para Débito, 2 para Crédito): "))
            if tipo_opcao == 1:
                tipo = "debito"
                specific_types = ['despesas', 'ativos', 'compras']
            elif tipo_opcao == 2:
                tipo = "credito"
                specific_types = ['passivos', 'entradas', 'vendas', 'patrimonio']
            else:
                print("Opção inválida!")
                return
        except ValueError:
            print("Entrada inválida. Digite um número.")
            return

        # Escolher o tipo específico
        print("\nEscolha o tipo específico:")
        for idx, st in enumerate(specific_types):
            print(f"{idx + 1}. {st}")
        try:
            specific_type_idx = int(input("Escolha uma opção: ")) - 1
            if 0 <= specific_type_idx < len(specific_types):
                specific_type = specific_types[specific_type_idx]
            else:
                print("Opção inválida!")
                return
        except ValueError:
            print("Entrada inválida. Digite um número.")
            return

        # Escolher a subcategoria
        specific_subtype = None
        if specific_type == "ativos":
            print("\nEscolha a subcategoria de ativos:")
            print("1. Ativo Circulante")
            print("2. Ativo Fixo")
            try:
                sub_type_idx = int(input("Escolha uma opção: ")) - 1
                if sub_type_idx == 0:
                    specific_subtype = "circulante"
                elif sub_type_idx == 1:
                    specific_subtype = "fixo"
                else:
                    print("Opção inválida!")
                    return
            except ValueError:
                print("Entrada inválida. Digite um número.")
                return
        elif specific_type == "passivos":
            print("\nEscolha a subcategoria de passivos:")
            print("1. Passivo Circulante")
            print("2. Passivo Não-Circulante")
            try:
                sub_type_idx = int(input("Escolha uma opção: ")) - 1
                if sub_type_idx == 0:
                    specific_subtype = "circulante"
                elif sub_type_idx == 1:
                    specific_subtype = "não-circulante"
                else:
                    print("Opção inválida!")
                    return
            except ValueError:
                print("Entrada inválida. Digite um número.")
                return

        # Mostrar categorias disponíveis
        categorias = self.visualizar_categorias()
        if not categorias:
            print("Nenhuma categoria cadastrada. Crie uma categoria antes de cadastrar uma conta.")
            return

        try:
            categoria_id = int(input("ID da categoria: "))
        except ValueError:
            print("Entrada inválida. Digite um número.")
            return

        # Inserir a conta no banco de dados
        try:
            sql = """
            INSERT INTO accounts (name, normalized_name, type, specific_type, specific_subtype, category_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db.execute(sql, (nome, nome_normalizado, tipo, specific_type, specific_subtype, categoria_id))
            create_backup()
            print("Conta cadastrada com sucesso!")
        except sqlite3.IntegrityError as e:
            print("Erro: Já existe uma conta com esse nome.")

    def visualizar_contas(self):
        print("\n--- Contas Cadastradas ---")
        sql = """
        SELECT a.id, a.name, a.type, a.specific_type, a.specific_subtype, c.name as categoria
        FROM accounts a
        JOIN account_categories c ON a.category_id = c.id
        """
        contas = self.db.execute(sql).fetchall()

        if not contas:
            print("Nenhuma conta cadastrada.")
            return None

        for conta in contas:
            print(f"ID: {conta[0]}")
            print(f"Nome: {conta[1]}")
            print(f"Tipo: {conta[2]} ({conta[3]})")
            if conta[4]:  # Exibir a subcategoria, se houver
                print(f"Subcategoria: {conta[4]}")
            print(f"Categoria: {conta[5]}")
            print("-" * 30)
        
        return contas

    def atualizar_conta(self):
        """
        Atualiza os dados de uma conta existente.
        Usa a função select_from_list para selecionar a conta.
        """
        print("\n--- Atualizar Conta ---")
        
        # Obtém a lista de contas
        contas = self.account_manager.get_accounts_by_name_or_id("")
        if not contas:
            print("Nenhuma conta cadastrada.")
            return
        
        # Seleciona a conta usando a função select_from_list
        conta_selecionada = select_from_list(contas, "Selecione a conta que deseja atualizar", key='name')
        if not conta_selecionada:
            return
        
        # Solicita os novos dados da conta
        novo_nome = input("Novo nome da conta: ").strip()
        if novo_nome == "":
            raise ValueError("Nome não pode estar em branco")
        print("\nEscolha o novo tipo de conta:")
        print("1. Débito")
        print("2. Crédito")
        try:
            tipo_opcao = int(input("Escolha uma opção (1 para Débito, 2 para Crédito): "))
            if tipo_opcao == 1:
                novo_tipo = "debito"
            elif tipo_opcao == 2:
                novo_tipo = "credito"
            else:
                print("Opção inválida!")
                return
        except ValueError:
            print("Entrada inválida. Digite um número.")
            return
        
        # Solicita o novo subtipo (se aplicável)
        novo_subtipo = None
        if novo_tipo == "debito":
            print("\nEscolha o novo subtipo de débito:")
            print("1. Ativo Circulante")
            print("2. Ativo Fixo")
            try:
                subtipo_opcao = int(input("Escolha uma opção: "))
                if subtipo_opcao == 1:
                    novo_subtipo = "circulante"
                elif subtipo_opcao == 2:
                    novo_subtipo = "fixo"
                else:
                    print("Opção inválida!")
                    return
            except ValueError:
                print("Entrada inválida. Digite um número.")
                return
        
        # Atualiza a conta no banco de dados
        if self.account_manager.update_account(conta_selecionada.id, novo_nome, novo_tipo, novo_subtipo):
            create_backup()
            print("Conta atualizada com sucesso!")
        else:
            print("Erro ao atualizar conta.")

    def excluir_conta(self):
        """
        Exclui uma conta existente.
        Usa a função select_from_list para selecionar a conta.
        """
        print("\n--- Excluir Conta ---")
        
        # Obtém a lista de contas
        contas = self.account_manager.get_accounts_by_name_or_id("")
        if not contas:
            print("Nenhuma conta cadastrada.")
            return
        
        # Seleciona a conta usando a função select_from_list
        conta_selecionada = select_from_list(contas, "Selecione a conta que deseja excluir")
        if not conta_selecionada:
            return
        
        # Confirma a exclusão
        confirma = input("Tem certeza que deseja excluir esta conta? (s/n): ").lower()
        if confirma == 's':
            if self.account_manager.delete_account(conta_selecionada.id):
                create_backup()
                print("Conta excluída com sucesso!")
            else:
                print("Erro ao excluir conta.")
        else:
            print("Operação cancelada.")