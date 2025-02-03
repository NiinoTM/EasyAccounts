from datetime import datetime
from decimal import Decimal
from src.database.connection import Database
from src.core.transactions import TransactionManager
from src.database.models import Transaction
from src.utils.validators import validate_date, validate_amount, validate_and_convert_date
from src.utils.formatters import format_currency, format_date, convert_comma_to_float
from typing import List, Optional
from src.utils.backup import create_backup
from src.utils.search_utils import select_from_list
from collections import namedtuple

class TransactionService:
    def __init__(self):
        self.db = Database()
        self.db.connect()
        self.transaction_manager = TransactionManager(self.db)

    def get_transactions_by_id_or_description(self, search_term: str) -> List[Transaction]:
        """
        Retrieves transactions that match the search term (ID or description).
        If search_term is empty, returns all transactions.
        """
        sql = """
        SELECT t.id, t.date, t.description, 
               d.name as debito, c.name as credito, 
               t.amount
        FROM transactions t
        JOIN accounts d ON t.debit_account = d.id
        JOIN accounts c ON t.credit_account = c.id
        WHERE t.id = ? OR t.description LIKE ?
        ORDER BY t.date DESC, t.id DESC
        """
        try:
            # Try to convert the search term to an integer (for ID search)
            transaction_id = int(search_term)
            results = self.db.execute(sql, (transaction_id, f"%{search_term}%")).fetchall()
        except ValueError:
            # If search term is not a number, search only by description
            if search_term.strip():  # If search_term is not empty
                results = self.db.execute(sql, (-1, f"%{search_term}%")).fetchall()
            else:
                # If search_term is empty, return all transactions
                sql_all = """
                SELECT t.id, t.date, t.description, 
                       d.name as debito, c.name as credito, 
                       t.amount
                FROM transactions t
                JOIN accounts d ON t.debit_account = d.id
                JOIN accounts c ON t.credit_account = c.id
                ORDER BY t.date DESC, t.id DESC
                """
                results = self.db.execute(sql_all).fetchall()

        return [Transaction(*result) for result in results]

    def nova_transacao(self):
        print("\n--- Nova Transação ---")
        
        # Get initial date in any format
        while True:
            data = input("Data da Transação (qualquer formato com dia, mês e ano): ").strip()
            data = validate_and_convert_date(data, "%Y-%m-%d")
            if data:
                print(f"Data convertida: {data}")
                break
            print("Data inválida. Certifique-se de incluir dia, mês e ano.")
            
        # Descrição
        descricao = input("Descrição: ")
        
        # Seleção de contas
        print("\nSeleção da conta de débito:")
        conta_debito = self.selecionar_conta("débito")
        if not conta_debito:
            return
            
        print("\nSeleção da conta de crédito:")
        conta_credito = self.selecionar_conta("crédito")
        if not conta_credito:
            return
            
        if conta_debito[0] == conta_credito[0]:
            print("Erro: A conta de débito e crédito não podem ser a mesma.")
            return
        
        # Valor
        try:
            valor = convert_comma_to_float((input("Valor: R$ ")))
            if valor <= 0:
                print("Erro: O valor deve ser maior que zero.")
                return
        except ValueError:
            print("Erro: Valor inválido.")
            return

        # Confirmação
        print("\nConfirme os dados da transação:")
        print(f"Data: {data}")
        print(f"Descrição: {descricao}")
        print(f"Débito: {conta_debito[1]} (ID: {conta_debito[0]})")
        print(f"Crédito: {conta_credito[1]} (ID: {conta_credito[0]})")
        print(f"Valor: R$ {valor:.2f}")
        
        confirma = input("\nConfirma a transação? (s/n): ").lower()
        if confirma != 's':
            print("Transação cancelada.")
            return

        # Inserir transação
        sql = """
        INSERT INTO transactions 
        (date, description, debit_account, credit_account, amount) 
        VALUES (?, ?, ?, ?, ?)
        """
        self.db.execute(sql, (data, descricao, conta_debito[0], conta_credito[0], valor))

        # Atualizar saldos
        self.db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", 
                    (valor, conta_debito[0]))
        self.db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", 
                    (valor, conta_credito[0]))

        print("\nTransação registrada com sucesso!")
        create_backup()


    def visualizar_transacoes(self):
        print("\n--- Transações Registradas ---")
        sql = """
        SELECT t.id, t.date, t.description, 
               d.name as debito, c.name as credito, 
               t.amount
        FROM transactions t
        JOIN accounts d ON t.debit_account = d.id
        JOIN accounts c ON t.credit_account = c.id
        ORDER BY t.date DESC, t.id DESC
        """
        transacoes = self.db.execute(sql).fetchall()

        if not transacoes:
            print("Nenhuma transação registrada.")
            return None

        print("\n{:<5} {:<12} {:<30} {:<20} {:<20} {:<15}".format(
            "ID", "Data", "Descrição", "Débito", "Crédito", "Valor"
        ))
        print("-" * 102)
        
        for t in transacoes:
            print("{:<5} {:<12} {:<30} {:<20} {:<20} R$ {:<12.2f}".format(
                t[0], t[1], t[2][:30], t[3][:20], t[4][:20], t[5]
            ))
        
        return transacoes
    
    def editar_transacao(self):
        # Mostrar transações existentes
        transacoes = self.visualizar_transacoes()
        if not transacoes:
            return

        # Selecionar transação
        search_term = input("\nDigite o ID ou descrição da transação que deseja editar (ou 'c' para cancelar): ").lower()
        if search_term == 'c':
            return
        
        # Buscar transações que correspondem ao termo de pesquisa
        transacoes_encontradas = self.get_transactions_by_id_or_description(search_term)
        if not transacoes_encontradas:
            print("Nenhuma transação encontrada.")
            return
        
        # Selecionar a transação usando a função select_from_list
        transacao_selecionada = select_from_list(transacoes_encontradas, "Selecione a transação que deseja editar")
        if not transacao_selecionada:
            return

        # Reverter saldos anteriores
        old_amount = transacao_selecionada.amount
        old_debito = transacao_selecionada.debit_account
        old_credito = transacao_selecionada.credit_account
        
        self.db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", 
                       (old_amount, old_debito))
        self.db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", 
                       (old_amount, old_credito))

        print("\nPreencha os novos dados (deixe em branco para manter o valor atual):")
        
        # Data
        nova_data = input(f"Nova data [{transacao_selecionada.date}]: ").strip()
        nova_data = nova_data if nova_data else transacao_selecionada.date
        
        # Descrição
        nova_desc = input(f"Nova descrição [{transacao_selecionada.description}]: ").strip()
        nova_desc = nova_desc if nova_desc else transacao_selecionada.description

        # Contas
        print("\nSeleção da nova conta de débito:")
        novo_debito_conta = self.selecionar_conta("de débito")
        if not novo_debito_conta:
            return
        novo_debito = novo_debito_conta[0]
        
        print("\nSeleção da nova conta de crédito:")
        novo_credito_conta = self.selecionar_conta("de crédito")
        if not novo_credito_conta:
            return
        novo_credito = novo_credito_conta[0]
        
        if novo_debito == novo_credito:
            print("Erro: A conta de débito e crédito não podem ser a mesma.")
            return
        
        # Valor
        try:
            novo_valor = input(f"Novo valor [R$ {old_amount:.2f}]: ").strip()
            novo_valor = float(novo_valor) if novo_valor else old_amount
            if novo_valor <= 0:
                print("Erro: O valor deve ser maior que zero.")
                return
        except ValueError:
            print("Erro: Valor inválido.")
            return

        # Confirmação
        print("\nConfirme os novos dados da transação:")
        print(f"Data: {nova_data}")
        print(f"Descrição: {nova_desc}")
        print(f"Débito: {novo_debito_conta[1]} (ID: {novo_debito})")
        print(f"Crédito: {novo_credito_conta[1]} (ID: {novo_credito})")
        print(f"Valor: R$ {novo_valor:.2f}")
        
        confirma = input("\nConfirma as alterações? (s/n): ").lower()
        if confirma != 's':
            print("Edição cancelada.")
            # Restaurar saldos originais
            self.db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", 
                          (old_amount, old_debito))
            self.db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", 
                          (old_amount, old_credito))
            return

        # Atualizar transação
        sql = """
        UPDATE transactions 
        SET date = ?, description = ?, debit_account = ?, 
            credit_account = ?, amount = ?
        WHERE id = ?
        """
        self.db.execute(sql, (nova_data, nova_desc, novo_debito, 
                            novo_credito, novo_valor, transacao_selecionada.id))

        # Atualizar novos saldos
        self.db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", 
                       (novo_valor, novo_debito))
        self.db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", 
                       (novo_valor, novo_credito))

        print("Transação atualizada com sucesso!")
        create_backup()

    def excluir_transacao(self):
        # Mostrar transações existentes
        transacoes = self.visualizar_transacoes()
        if not transacoes:
            return

        # Selecionar transação
        search_term = input("\nDigite o ID ou descrição da transação que deseja excluir (ou 'c' para cancelar): ").lower()
        if search_term == 'c':
            return
        
        # Buscar transações que correspondem ao termo de pesquisa
        transacoes_encontradas = self.get_transactions_by_id_or_description(search_term)
        if not transacoes_encontradas:
            print("Nenhuma transação encontrada.")
            return
        
        # Selecionar a transação usando a função select_from_list
        transacao_selecionada = select_from_list(transacoes_encontradas, "Selecione a transação que deseja excluir")
        if not transacao_selecionada:
            return

        # Mostrar detalhes da transação
        print("\nDetalhes da transação a ser excluída:")
        print(f"Data: {transacao_selecionada.date}")
        print(f"Descrição: {transacao_selecionada.description}")
        print(f"Conta de Débito: {transacao_selecionada.debit_account}")
        print(f"Conta de Crédito: {transacao_selecionada.credit_account}")
        print(f"Valor: R$ {transacao_selecionada.amount:.2f}")
        
        confirma = input("\nConfirma a exclusão desta transação? (s/n): ").lower()
        if confirma != 's':
            print("Exclusão cancelada.")
            return

        # Reverter saldos
        valor = transacao_selecionada.amount
        conta_debito = transacao_selecionada.debit_account
        conta_credito = transacao_selecionada.credit_account
        
        self.db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", 
                       (valor, conta_debito))
        self.db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", 
                       (valor, conta_credito))

        # Excluir transação
        sql = "DELETE FROM transactions WHERE id = ?"
        self.db.execute(sql, (transacao_selecionada.id,))
        
        print("Transação excluída com sucesso!")
        create_backup()
    
    from src.utils.search_utils import select_from_list

    def selecionar_conta(self, tipo):
        """
        Interativamente pesquisa e seleciona uma conta.
        
        Args:
            tipo (str): Tipo de conta (e.g., "débito", "crédito")
        
        Returns:
            tuple: (id, nome) da conta selecionada ou None se cancelado
        """
        # Definir a estrutura de dados Account
        Account = namedtuple('Account', ['id', 'name', 'balance'])

        # Buscar todas as contas
        sql = "SELECT id, name, balance FROM accounts ORDER BY name"
        contas = self.db.execute(sql).fetchall()
        
        if not contas:
            print("Nenhuma conta cadastrada.")
            return None

        # Criar lista de objetos Account
        contas_list = [Account(id=conta[0], name=conta[1], balance=conta[2]) for conta in contas]

        # Usar a função select_from_list para selecionar a conta
        conta_selecionada = select_from_list(contas_list, f"Selecione a conta de {tipo}", key='name')
        if conta_selecionada:
            return (conta_selecionada.id, conta_selecionada.name)
        return None

    def buscar_conta(self, conta_id):
        """
        Busca uma conta pelo ID
        
        Args:
            conta_id (int): ID da conta
            
        Returns:
            tuple: (id, nome) da conta ou None se não encontrada
        """
        sql = "SELECT id, name FROM accounts WHERE id = ?"
        result = self.db.execute(sql, (conta_id,)).fetchone()
        return result if result else None