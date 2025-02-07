from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from src.database.connection import Database
from src.database.models import Asset, DepreciationMethod
from src.utils.validators import validate_and_convert_date
from src.utils.formatters import format_currency
from src.utils.search_utils import select_from_list
from src.services.fiscal_period_service import FiscalPeriodService

class DepreciationService:
    def __init__(self):
        self.db = Database()
        self.db.connect()
        self.setup_depreciation_methods()
        self.create_tables()
        self.fiscal_period_service = FiscalPeriodService()

    def create_tables(self):
        # Create depreciation_methods table
        sql_depreciation_methods = """
        CREATE TABLE IF NOT EXISTS depreciation_methods (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            annual_rate REAL
        );"""

        # Create assets table
        sql_assets = """
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            acquisition_date TEXT NOT NULL,
            acquisition_value REAL NOT NULL,
            depreciation_method_id INTEGER,
            useful_life_years INTEGER,
            salvage_value REAL,
            start_depreciation_date TEXT NOT NULL,
            account_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (depreciation_method_id) REFERENCES depreciation_methods(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        );"""

        self.db.execute(sql_depreciation_methods)
        self.db.execute(sql_assets)

    def setup_depreciation_methods(self):
        """Initialize predefined depreciation methods."""
        methods = [
            ("Linear", "Depreciation is spread evenly across the asset's useful life", 0),
            ("Declining Balance", "Accelerated depreciation with higher initial amounts", 2),
            ("Sum of Years Digits", "Accelerated depreciation based on remaining life", 0),
        ]

        sql = "INSERT OR IGNORE INTO depreciation_methods (name, description, annual_rate) VALUES (?, ?, ?)"
        for method in methods:
            self.db.execute(sql, method)

    def calcular_valor_atual(self, asset, reference_date=None):
        today = reference_date or datetime.now().date()
        start_date = datetime.strptime(asset[7], '%Y-%m-%d').date()
        acquisition_value = asset[3]
        salvage_value = asset[6]
        useful_life_years = asset[5]
        method_name = asset[4]

        if start_date > today:
            return acquisition_value

        dias_decorridos = (today - start_date).days
        anos_decorridos = dias_decorridos / 365.25

        if anos_decorridos >= useful_life_years:
            return salvage_value

        valor_depreciavel = acquisition_value - salvage_value

        if method_name == "Linear":
            depreciacao_acumulada = valor_depreciavel * (anos_decorridos / useful_life_years)
        elif method_name == "Declining Balance":
            taxa = 2 / useful_life_years
            valor_atual = acquisition_value * ((1 - taxa) ** anos_decorridos)
            return max(valor_atual, salvage_value)
        elif method_name == "Sum of Years Digits":
            soma_anos = (useful_life_years * (useful_life_years + 1)) / 2
            anos_restantes = useful_life_years - anos_decorridos
            depreciacao_acumulada = valor_depreciavel * (1 - (anos_restantes * (anos_restantes + 1)) / soma_anos)
        else:
            return acquisition_value

        valor_atual = acquisition_value - depreciacao_acumulada
        return max(valor_atual, salvage_value)



    def visualizar_ativos(self):
        print("\n=== Ativos Cadastrados ===")
        
        sql = """
        SELECT a.id, a.name, a.acquisition_date, a.acquisition_value,
               dm.name as method_name, a.useful_life_years, a.salvage_value,
               a.start_depreciation_date, acc.name as account_name, a.is_active
        FROM assets a
        JOIN depreciation_methods dm ON a.depreciation_method_id = dm.id
        JOIN accounts acc ON a.account_id = acc.id
        ORDER BY a.acquisition_date DESC
        """
        assets = self.db.execute(sql).fetchall()

        if not assets:
            print("Nenhum ativo cadastrado.")
            return

        print("\n{:<5} {:<20} {:<12} {:<15} {:<15} {:<10} {:<15} {:<15} {:<20} {:<8}".format(
            "ID", "Nome", "Aquisição", "Valor Aquis.", "Valor Atual", "Vida Útil",
            "Valor Resid.", "Início Depr.", "Conta", "Ativo"
        ))
        print("-" * 140)

        for asset in assets:
            valor_atual = self.calcular_valor_atual(asset)
            depreciacao_acumulada = asset[3] - valor_atual  # Valor de aquisição - Valor atual
            percentual_depreciado = (depreciacao_acumulada / asset[3]) * 100 if asset[3] > 0 else 0

            print("{:<5} {:<20} {:<12} R$ {:<12.2f} R$ {:<12.2f} {:<10} R$ {:<12.2f} {:<12} {:<20} {:<8}".format(
                asset[0],
                asset[1][:20],
                datetime.strptime(asset[2], '%Y-%m-%d').strftime('%d/%m/%Y'),
                asset[3],  # Valor de aquisição
                valor_atual,  # Valor atual calculado
                f"{asset[5]} anos",
                asset[6],  # Valor residual
                datetime.strptime(asset[7], '%Y-%m-%d').strftime('%d/%m/%Y'),
                asset[8][:20],
                "Sim" if asset[9] else "Não"
            ))
            print(f"   → Depreciação acumulada: R$ {depreciacao_acumulada:.2f} ({percentual_depreciado:.1f}%)")
            print("-" * 140)

        return assets

    def cadastrar_ativo(self):
        print("\n=== Cadastrar Novo Ativo ===")
        
        # Get asset information
        name = input("Nome do ativo: ")
        
        # Get acquisition date
        while True:
            acquisition_date = input("Data de aquisição (qualquer formato com dia, mês e ano): ")
            formatted_date = validate_and_convert_date(acquisition_date, "%Y-%m-%d")
            if formatted_date:
                break
            print("Data inválida. Tente novamente.")

        # Get acquisition value
        while True:
            try:
                acquisition_value = float(input("Valor de aquisição: R$ ").replace(',', '.'))
                if acquisition_value <= 0:
                    print("O valor deve ser maior que zero.")
                    continue
                break
            except ValueError:
                print("Valor inválido. Use apenas números.")

        # Select depreciation method
        sql = "SELECT id, name, description FROM depreciation_methods"
        methods = self.db.execute(sql).fetchall()
        print("\nMétodos de depreciação disponíveis:")
        for method in methods:
            print(f"{method[0]}. {method[1]} - {method[2]}")
        
        while True:
            try:
                method_id = int(input("Selecione o método de depreciação: "))
                if any(method[0] == method_id for method in methods):
                    break
                print("Método inválido.")
            except ValueError:
                print("Digite um número válido.")

        # Get useful life
        while True:
            try:
                useful_life = int(input("Vida útil (em anos): "))
                if useful_life <= 0:
                    print("A vida útil deve ser maior que zero.")
                    continue
                break
            except ValueError:
                print("Digite um número válido.")

        # Get salvage value
        while True:
            try:
                salvage_value = float(input("Valor residual: R$ ").replace(',', '.'))
                if salvage_value < 0:
                    print("O valor residual não pode ser negativo.")
                    continue
                if salvage_value >= acquisition_value:
                    print("O valor residual deve ser menor que o valor de aquisição.")
                    continue
                break
            except ValueError:
                print("Valor inválido. Use apenas números.")

        # Get start depreciation date
        while True:
            start_date = input("Data de início da depreciação (qualquer formato com dia, mês e ano): ")
            formatted_start_date = validate_and_convert_date(start_date, "%Y-%m-%d")
            if formatted_start_date:
                break
            print("Data inválida. Tente novamente.")

        # Select account
        print("\nSelecione a conta do ativo:")
        from src.services.transaction_service import TransactionService
        transaction_service = TransactionService()
        account = transaction_service.selecionar_conta("ativo")
        if not account:
            print("Operação cancelada.")
            return

        # Confirm information
        print("\nConfirme as informações do ativo:")
        print(f"Nome: {name}")
        print(f"Data de aquisição: {formatted_date}")
        print(f"Valor de aquisição: R$ {acquisition_value:.2f}")
        print(f"Método de depreciação: {next(m[1] for m in methods if m[0] == method_id)}")
        print(f"Vida útil: {useful_life} anos")
        print(f"Valor residual: R$ {salvage_value:.2f}")
        print(f"Data de início da depreciação: {formatted_start_date}")
        print(f"Conta: {account[1]}")

        if input("\nConfirmar cadastro? (s/n): ").lower() != 's':
            print("Operação cancelada.")
            return

        # Save asset
        sql = """
        INSERT INTO assets (
            name, acquisition_date, acquisition_value, depreciation_method_id,
            useful_life_years, salvage_value, start_depreciation_date, account_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(sql, (
            name, formatted_date, acquisition_value, method_id,
            useful_life, salvage_value, formatted_start_date, account[0]
        ))
        print("\nAtivo cadastrado com sucesso!")

    def calcular_depreciacao(self):
        print("\n=== Calcular Depreciação para Período Fiscal ===")
        # Consulta os ativos ativos de forma resumida para seleção
        sql = """
        SELECT a.id, a.name, a.acquisition_date, a.acquisition_value,
            dm.name as method_name, a.useful_life_years, a.salvage_value,
            a.start_depreciation_date, acc.name as account_name
        FROM assets a
        JOIN depreciation_methods dm ON a.depreciation_method_id = dm.id
        JOIN accounts acc ON a.account_id = acc.id
        WHERE a.is_active = 1
        """
        assets = self.db.execute(sql).fetchall()
        if not assets:
            print("Nenhum ativo cadastrado.")
            return

        print("\nAtivos disponíveis:")
        for idx, asset in enumerate(assets, 1):
            print(f"{idx}. {asset[1]} (Método: {asset[4]})")

        while True:
            try:
                choice = int(input("\nSelecione o ativo para calcular a depreciação: ")) - 1
                if 0 <= choice < len(assets):
                    break
                print("Opção inválida.")
            except ValueError:
                print("Digite um número válido.")
        asset = assets[choice]

        # Obtém o período fiscal corrente (data de início e de fim)
        fiscal_period = self.fiscal_period_service.get_current_period()
        if not fiscal_period:
            print("Nenhum período fiscal encontrado.")
            return
        start_date = datetime.strptime(fiscal_period[1], '%Y-%m-%d').date()
        end_date = datetime.strptime(fiscal_period[2], '%Y-%m-%d').date()

        # Calcula o valor do ativo na data de início e na data de fim do período
        valor_inicio = self.calcular_valor_atual(asset, start_date)
        valor_fim = self.calcular_valor_atual(asset, end_date)
        # Depreciação acumulada no período é a diferença entre o valor no início e no fim
        depreciacao_total = valor_inicio - valor_fim

        # Cálculo da depreciação anual e mensal de acordo com o método cadastrado
        method_name = asset[4]
        if method_name == "Linear":
            # A depreciação anual é calculada dividindo a diferença entre o valor de aquisição e o valor residual pela vida útil.
            anual_depreciacao = (asset[3] - asset[6]) / asset[5]
        elif method_name == "Declining Balance":
            # Para saldo decrescente, a taxa é o quociente de dois pela vida útil.
            taxa = 2 / asset[5]
            # A depreciação anual estimada é o valor no início do período multiplicado pela taxa.
            anual_depreciacao = valor_inicio * taxa
        elif method_name == "Sum of Years Digits":
            # Calcula o ano corrente de depreciação com base na data de início da depreciação
            start_depr_date = datetime.strptime(asset[7], '%Y-%m-%d').date()
            anos_decorridos = (start_date - start_depr_date).days / 365.25
            current_year = int(anos_decorridos) + 1
            total_years = asset[5]
            if current_year > total_years:
                anual_depreciacao = 0
            else:
                # A soma dos dígitos é obtida multiplicando a vida útil pelo valor da vida útil mais um e dividindo por dois.
                soma_anos = total_years * (total_years + 1) / 2
                # A depreciação anual é calculada multiplicando a base depreciável pela fração dos anos restantes sobre a soma dos dígitos.
                anual_depreciacao = ((total_years - current_year + 1) / soma_anos) * (asset[3] - asset[6])
        else:
            anual_depreciacao = 0

        mensal_depreciacao = anual_depreciacao / 12

        print(f"\nDepreciação do ativo {asset[1]} para o período fiscal:")
        print(f"Valor no início (em {start_date.strftime('%d/%m/%Y')}): R$ {valor_inicio:.2f}")
        print(f"Valor no final (em {end_date.strftime('%d/%m/%Y')}): R$ {valor_fim:.2f}")
        print(f"Depreciação acumulada no período: R$ {depreciacao_total:.2f}")
        print(f"Depreciação anual estimada ({method_name}): R$ {anual_depreciacao:.2f}")
        print(f"Depreciação mensal estimada ({method_name}): R$ {mensal_depreciacao:.2f}")

        # Registra a transação, se o usuário desejar, usando a data final do período fiscal e o valor acumulado
        if input("\nDeseja registrar a depreciação como transação? (s/n): ").lower() == 's':
            print("\nSelecione a conta de débito (despesa de depreciação):")
            from src.services.transaction_service import TransactionService
            ts = TransactionService()
            debit_account = ts.selecionar_conta("débito")
            if not debit_account:
                return

            print("\nSelecione a conta de crédito (depreciação acumulada):")
            credit_account = ts.selecionar_conta("crédito")
            if not credit_account:
                return

            description = f"Depreciação acumulada no período - {asset[1]}"
            sql = """
            INSERT INTO transactions (date, description, debit_account, credit_account, amount)
            VALUES (?, ?, ?, ?, ?)
            """
            transaction_date = end_date.strftime("%Y-%m-%d")
            self.db.execute(sql, (transaction_date, description, debit_account[0], credit_account[0], depreciacao_total))
            self.db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", 
                            (depreciacao_total, debit_account[0]))
            self.db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", 
                            (depreciacao_total, credit_account[0]))
            print("\nTransação de depreciação registrada com sucesso!")


    def calcular_depreciacao_por_periodo(self):
        print("\n=== Calcular Depreciação por Período Fiscal ===")
        assets = self.visualizar_ativos()
        if not assets:
            return

        while True:
            try:
                choice = int(input("\nSelecione o ativo para calcular a depreciação: ")) - 1
                if 0 <= choice < len(assets):
                    break
                print("Opção inválida.")
            except ValueError:
                print("Digite um número válido.")

        asset = assets[choice]
        fiscal_period = self.fiscal_period_service.get_current_period()

        if not fiscal_period:
            print("Nenhum período fiscal encontrado.")
            return

        start_date = datetime.strptime(fiscal_period[1], '%Y-%m-%d').date()
        end_date = datetime.strptime(fiscal_period[2], '%Y-%m-%d').date()

        valor_inicio = self.calcular_valor_atual(asset, start_date)
        valor_fim = self.calcular_valor_atual(asset, end_date)
        depreciacao_total = valor_inicio - valor_fim
        anual_depreciacao = (asset[3] - asset[6]) / asset[5]
        mensal_depreciacao = anual_depreciacao / 12

        print(f"\nDepreciação do ativo {asset[1]} para o período fiscal:")
        print(f"Valor no início: R$ {valor_inicio:.2f}")
        print(f"Valor no final: R$ {valor_fim:.2f}")
        print(f"Depreciação anual: R$ {anual_depreciacao:.2f}")
        print(f"Depreciação mensal: R$ {mensal_depreciacao:.2f}")
        print(f"Depreciação acumulada no período: R$ {depreciacao_total:.2f}")

    def visualizar_ativos(self):
        print("\n=== Ativos Cadastrados ===")
        
        sql = """
        SELECT a.id, a.name, a.acquisition_date, a.acquisition_value,
               dm.name as method_name, a.useful_life_years, a.salvage_value,
               a.start_depreciation_date, acc.name as account_name, a.is_active
        FROM assets a
        JOIN depreciation_methods dm ON a.depreciation_method_id = dm.id
        JOIN accounts acc ON a.account_id = acc.id
        ORDER BY a.acquisition_date DESC
        """
        assets = self.db.execute(sql).fetchall()

        if not assets:
            print("Nenhum ativo cadastrado.")
            return

        print("\n{:<5} {:<20} {:<12} {:<15} {:<20} {:<10} {:<15} {:<12} {:<20} {:<8}".format(
            "ID", "Nome", "Aquisição", "Valor", "Método", "Vida Útil",
            "Valor Residual", "Início Depr.", "Conta", "Ativo"
        ))
        print("-" * 140)

        for asset in assets:
            print("{:<5} {:<20} {:<12} R$ {:<12.2f} {:<20} {:<10} R$ {:<12.2f} {:<12} {:<20} {:<8}".format(
                asset[0], asset[1][:20], asset[2], asset[3], asset[4][:20],
                f"{asset[5]} anos", asset[6], asset[7], asset[8][:20],
                "Sim" if asset[9] else "Não"
            ))