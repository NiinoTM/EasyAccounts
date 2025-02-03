from src.database.connection import Database
from src.core.templates import TransactionTemplate, TemplateTransaction
from src.services.transaction_service import TransactionService
from src.utils.search_utils import select_from_list
from src.utils.formatters import convert_comma_to_float
from src.utils.backup import create_backup
from collections import namedtuple
from datetime import datetime

from typing import List
import json

class TemplateService:
    def __init__(self):
        self.db = Database()
        self.db.connect()
        self.transaction_service = TransactionService()

    def get_templates_by_name_or_id(self, search_term: str) -> List[TransactionTemplate]:
        """
        Retrieves templates that match the search term (ID or name).
        If search_term is empty, returns all templates.
        """
        sql = """
        SELECT id, name, details 
        FROM transaction_templates 
        WHERE id = ? OR name LIKE ?
        """
        try:
            # Try to convert the search term to an integer (for ID search)
            template_id = int(search_term)
            results = self.db.execute(sql, (template_id, f"%{search_term}%")).fetchall()
        except ValueError:
            # If search term is not a number, search only by name
            if search_term.strip():  # If search_term is not empty
                results = self.db.execute(sql, (-1, f"%{search_term}%")).fetchall()
            else:
                # If search_term is empty, return all templates
                sql_all = "SELECT id, name, details FROM transaction_templates"
                results = self.db.execute(sql_all).fetchall()

        # Convert results to TransactionTemplate objects
        templates = []
        for result in results:
            template = TransactionTemplate.from_json(result[0], result[1], result[2])
            templates.append(template)

        return templates

    def novo_modelo(self):
        """Creates a new transaction template."""
        print("\n=== Criar Novo Modelo de Transações ===")
        nome = input("Nome do modelo: ")
        
        transactions = []
        while True:
            print("\n--- Adicionar Transação ao Modelo ---")
            
            # Selecionar conta de débito
            print("\nSeleção da conta de débito:")
            conta_debito = self.transaction_service.selecionar_conta("de débito")
            if not conta_debito:
                return
            
            # Selecionar conta de crédito
            print("\nSeleção da conta de crédito:")
            conta_credito = self.transaction_service.selecionar_conta("de crédito")
            if not conta_credito:
                return
            
            if conta_debito[0] == conta_credito[0]:
                print("Erro: A conta de débito e crédito não podem ser a mesma.")
                continue
            
            # Pegar descrição e valor
            descricao = input("Descrição da transação: ")
            try:
                valor = float(input("Valor: R$ "))
                if valor <= 0:
                    print("Erro: O valor deve ser maior que zero.")
                    continue
            except ValueError:
                print("Erro: Valor inválido.")
                continue

            # Criar transação do template
            template_transaction = TemplateTransaction(
                description=descricao,
                debit_account=conta_debito[0],
                credit_account=conta_credito[0],
                amount=valor
            )
            transactions.append(template_transaction)

            # Perguntar se quer adicionar mais transações
            mais = input("\nDeseja adicionar mais uma transação ao modelo? (s/n): ").lower()
            if mais != 's':
                break

        # Criar e salvar o template
        template = TransactionTemplate(name=nome, transactions=transactions)
        
        sql = "INSERT INTO transaction_templates (name, details) VALUES (?, ?)"
        self.db.execute(sql, (nome, template.to_json()))
        create_backup()
        print("\nModelo criado com sucesso!")

    def visualizar_modelos(self):
        """Lista todos os modelos disponíveis"""
        print("\n=== Modelos de Transações Disponíveis ===")
        
        sql = "SELECT id, name, details FROM transaction_templates ORDER BY name"
        modelos = self.db.execute(sql).fetchall()
        
        if not modelos:
            print("Nenhum modelo cadastrado.")
            return None
        
        print("\n{:<5} {:<30}".format("ID", "Nome"))
        print("-" * 35)
        
        for modelo in modelos:
            print(f"{modelo[0]:<5} {modelo[1]:<30}")
            template = TransactionTemplate.from_json(modelo[0], modelo[1], modelo[2])
            
            print("\nTransações no modelo:")
            for idx, trans in enumerate(template.transactions, 1):
                print(f"\n  Transação {idx}:")
                conta_debito = self.transaction_service.buscar_conta(trans.debit_account)
                conta_credito = self.transaction_service.buscar_conta(trans.credit_account)
                print(f"  Descrição: {trans.description}")
                print(f"  Débito: {conta_debito[1]}")
                print(f"  Crédito: {conta_credito[1]}")
                print(f"  Valor: R$ {trans.amount:.2f}")
            print("\n" + "-" * 35)
        
        return modelos

    def executar_modelo(self):
        """Executa um modelo de transações com opção de modificar valores"""
        modelos = self.visualizar_modelos()
        if not modelos:
            return

        # Define a estrutura de dados Modelo
        Modelo = namedtuple('Modelo', ['id', 'name', 'details'])

        # Criar lista de objetos Modelo
        modelos_list = [Modelo(id=modelo[0], name=modelo[1], details=modelo[2]) for modelo in modelos]

        # Usar a função select_from_list para selecionar o modelo
        modelo_selecionado = select_from_list(modelos_list, "Selecione o modelo que deseja executar", key='name')
        if not modelo_selecionado:
            return

        # Buscar o modelo
        sql = "SELECT id, name, details FROM transaction_templates WHERE id = ?"
        result = self.db.execute(sql, (modelo_selecionado.id,)).fetchone()
        
        if not result:
            print("Erro: Modelo não encontrado.")
            return

        template = TransactionTemplate.from_json(result[0], result[1], result[2])
        
        # Lista para armazenar os novos valores
        new_transactions = []
        
        # Confirmar e possivelmente modificar cada transação
        print("\nRevisão das transações do modelo:")
        for idx, trans in enumerate(template.transactions, 1):
            conta_debito = self.transaction_service.buscar_conta(trans.debit_account)
            conta_credito = self.transaction_service.buscar_conta(trans.credit_account)
            
            print(f"\nTransação {idx}:")
            print(f"Descrição: {trans.description}")
            print(f"Débito: {conta_debito[1]} (ID: {conta_debito[0]})")
            print(f"Crédito: {conta_credito[1]} (ID: {conta_credito[0]})")
            print(f"Valor original: R$ {trans.amount:.2f}")

            modificar = input("Deseja modificar o valor desta transação? (s/n): ").lower()
            
            if modificar == 's':
                while True:
                    try:
                        novo_valor = convert_comma_to_float(input("Digite o novo valor: R$ "))
                        if novo_valor <= 0:
                            print("Erro: O valor deve ser maior que zero.")
                            continue
                        break
                    except ValueError:
                        print("Erro: Digite um valor numérico válido.")
            else:
                novo_valor = trans.amount

            new_transactions.append(TemplateTransaction(
                description=trans.description,
                debit_account=trans.debit_account,
                credit_account=trans.credit_account,
                amount=novo_valor
            ))

        # Mostrar resumo final
        print("\nResumo final das transações a serem executadas:")
        for idx, trans in enumerate(new_transactions, 1):
            conta_debito = self.transaction_service.buscar_conta(trans.debit_account)
            conta_credito = self.transaction_service.buscar_conta(trans.credit_account)
            
            print(f"\nTransação {idx}:")
            print(f"Descrição: {trans.description}")
            print(f"Débito: {conta_debito[1]}")
            print(f"Crédito: {conta_credito[1]}")
            print(f"Valor: R$ {trans.amount:.2f}")

        confirma = input("\nConfirma a execução dessas transações? (s/n): ").lower()
        if confirma != 's':
            print("Execução cancelada.")
            return

        # Executar todas as transações
        data = datetime.now().strftime("%Y-%m-%d")
        for trans in new_transactions:
            sql = """
            INSERT INTO transactions 
            (date, description, debit_account, credit_account, amount) 
            VALUES (?, ?, ?, ?, ?)
            """
            self.db.execute(sql, (
                data,
                trans.description,
                trans.debit_account,
                trans.credit_account,
                trans.amount
            ))

            # Atualizar saldos
            self.db.execute(
                "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                (trans.amount, trans.debit_account)
            )
            self.db.execute(
                "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                (trans.amount, trans.credit_account)
            )

        print("\nModelo executado com sucesso!")

    def editar_modelo(self):
        """Edita um modelo existente."""
        print("\n=== Editar Modelo ===")
        
        # Obtém a lista de modelos
        modelos = self.get_templates_by_name_or_id("")
        if not modelos:
            print("Nenhum modelo cadastrado.")
            return
        
        # Seleciona o modelo usando a função select_from_list
        modelo_selecionado = select_from_list(modelos, "Selecione o modelo que deseja editar")
        if not modelo_selecionado:
            return
        
        # Mostra as transações atuais do modelo
        print("\nTransações atuais do modelo '{}':".format(modelo_selecionado.name))
        for idx, trans in enumerate(modelo_selecionado.transactions, 1):
            print(f"\nTransação {idx}:")
            conta_debito = self.transaction_service.buscar_conta(trans.debit_account)
            conta_credito = self.transaction_service.buscar_conta(trans.credit_account)
            print(f"Descrição: {trans.description}")
            print(f"Débito: {conta_debito[1]} (ID: {conta_debito[0]})")
            print(f"Crédito: {conta_credito[1]} (ID: {conta_credito[0]})")
            print(f"Valor: R$ {trans.amount:.2f}")
        
        # Pergunta se deseja editar o nome do modelo
        novo_nome = input(f"\nNovo nome do modelo [{modelo_selecionado.name}]: ").strip()
        if not novo_nome:
            novo_nome = modelo_selecionado.name  # Mantém o nome atual se nada for digitado
        
        # Pergunta se deseja editar as transações
        novas_transacoes = []
        for idx, trans in enumerate(modelo_selecionado.transactions, 1):
            print(f"\nEditando Transação {idx}:")
            print(f"Descrição atual: {trans.description}")
            print(f"Débito atual: {conta_debito[1]} (ID: {conta_debito[0]})")
            print(f"Crédito atual: {conta_credito[1]} (ID: {conta_credito[0]})")
            print(f"Valor atual: R$ {trans.amount:.2f}")
            
            # Pergunta se deseja manter a transação
            manter = input("\nDeseja manter esta transação? (s/n): ").lower()
            if manter == 's':
                novas_transacoes.append(trans)
            else:
                # Permite editar a transação
                nova_descricao = input(f"Nova descrição [{trans.description}]: ").strip()
                if not nova_descricao:
                    nova_descricao = trans.description
                
                # Selecionar nova conta de débito
                print("\nSeleção da nova conta de débito:")
                nova_conta_debito = self.transaction_service.selecionar_conta("de débito")
                if not nova_conta_debito:
                    continue
                
                # Selecionar nova conta de crédito
                print("\nSeleção da nova conta de crédito:")
                nova_conta_credito = self.transaction_service.selecionar_conta("de crédito")
                if not nova_conta_credito:
                    continue
                
                if nova_conta_debito[0] == nova_conta_credito[0]:
                    print("Erro: A conta de débito e crédito não podem ser a mesma.")
                    continue
                
                # Pegar novo valor
                try:
                    novo_valor = input(f"Novo valor [R$ {trans.amount:.2f}]: ").strip()
                    novo_valor = float(novo_valor) if novo_valor else trans.amount
                    if novo_valor <= 0:
                        print("Erro: O valor deve ser maior que zero.")
                        continue
                except ValueError:
                    print("Erro: Valor inválido.")
                    continue
                
                # Criar nova transação
                nova_transacao = TemplateTransaction(
                    description=nova_descricao,
                    debit_account=nova_conta_debito[0],
                    credit_account=nova_conta_credito[0],
                    amount=novo_valor
                )
                novas_transacoes.append(nova_transacao)
        
        # Pergunta se deseja adicionar novas transações
        while True:
            adicionar = input("\nDeseja adicionar uma nova transação? (s/n): ").lower()
            if adicionar != 's':
                break
            
            # Adicionar nova transação
            print("\n--- Adicionar Nova Transação ---")
            
            # Selecionar conta de débito
            print("\nSeleção da conta de débito:")
            conta_debito = self.transaction_service.selecionar_conta("de débito")
            if not conta_debito:
                continue
            
            # Selecionar conta de crédito
            print("\nSeleção da conta de crédito:")
            conta_credito = self.transaction_service.selecionar_conta("de crédito")
            if not conta_credito:
                continue
            
            if conta_debito[0] == conta_credito[0]:
                print("Erro: A conta de débito e crédito não podem ser a mesma.")
                continue
            
            # Pegar descrição e valor
            descricao = input("Descrição da transação: ")
            try:
                valor = float(input("Valor: R$ "))
                if valor <= 0:
                    print("Erro: O valor deve ser maior que zero.")
                    continue
            except ValueError:
                print("Erro: Valor inválido.")
                continue
            
            # Criar nova transação
            nova_transacao = TemplateTransaction(
                description=descricao,
                debit_account=conta_debito[0],
                credit_account=conta_credito[0],
                amount=valor
            )
            novas_transacoes.append(nova_transacao)
        
        # Atualizar o modelo
        modelo_selecionado.name = novo_nome
        modelo_selecionado.transactions = novas_transacoes
        
        # Salvar no banco de dados
        sql = "UPDATE transaction_templates SET name = ?, details = ? WHERE id = ?"
        self.db.execute(sql, (novo_nome, modelo_selecionado.to_json(), modelo_selecionado.id))
        create_backup()
        print("\nModelo atualizado com sucesso!")

    def excluir_modelo(self):
        """Exclui um modelo existente."""
        print("\n=== Excluir Modelo ===")
        
        # Obtém a lista de modelos
        modelos = self.get_templates_by_name_or_id("")
        if not modelos:
            print("Nenhum modelo cadastrado.")
            return
        
        # Seleciona o modelo usando a função select_from_list
        modelo_selecionado = select_from_list(modelos, "Selecione o modelo que deseja excluir")
        if not modelo_selecionado:
            return
        
        # Confirma a exclusão
        confirma = input("Tem certeza que deseja excluir o modelo '{}'? (s/n): ".format(modelo_selecionado.name)).lower()
        if confirma == 's':
            sql = "DELETE FROM transaction_templates WHERE id = ?"
            self.db.execute(sql, (modelo_selecionado.id,))
            create_backup()
            print("\nModelo excluído com sucesso!")
        else:
            print("Operação cancelada.")
