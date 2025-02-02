# src/services/fiscal_period_service.py
from datetime import datetime, timedelta
from src.database.connection import Database
from src.utils.validators import validate_date

class FiscalPeriodService:
    def __init__(self):
        self.db = Database()
        self.db.connect()

    def cadastrar_periodo(self):
        print("\n=== Cadastrar Período de Exercício ===")
        
        # Get initial date in DD-MM-YYYY format
        while True:
            data_inicial = input("Data inicial (DD-MM-YYYY): ").strip()
            if validate_date(data_inicial, format="%d-%m-%Y"):
                break
            print("Data inválida. Use o formato DD-MM-YYYY.")

        # Get interval type
        print("\nTipo de intervalo:")
        print("1. Mensal (30 dias)")
        print("2. Trimestral (90 dias)")
        print("3. Semestral (180 dias)")
        print("4. Anual (365 dias)")
        print("5. Personalizado")

        try:
            opcao = int(input("\nEscolha uma opção: "))
            if opcao == 5:
                while True:
                    try:
                        intervalo = int(input("Digite o intervalo em dias: "))
                        if intervalo > 0:
                            break
                        print("O intervalo deve ser maior que zero.")
                    except ValueError:
                        print("Por favor, digite um número válido.")
            else:
                intervalos = {1: 30, 2: 90, 3: 180, 4: 365}
                intervalo = intervalos.get(opcao)
                if not intervalo:
                    print("Opção inválida!")
                    return

            # Calculate end date
            data_inicial_obj = datetime.strptime(data_inicial, '%d-%m-%Y')
            data_final_obj = data_inicial_obj + timedelta(days=intervalo)
            data_final = data_final_obj.strftime('%d-%m-%Y')

            # Show summary in DD-MM-YYYY format
            print("\nResumo do período:")
            print(f"Data inicial: {data_inicial}")
            print(f"Data final: {data_final}")
            print(f"Intervalo: {intervalo} dias")

            confirma = input("\nConfirmar cadastro? (s/n): ").lower()
            if confirma != 's':
                print("Operação cancelada.")
                return

            # Save to database in YYYY-MM-DD format
            sql = """
            INSERT INTO fiscal_periods (start_date, end_date, interval_days)
            VALUES (?, ?, ?)
            """
            self.db.execute(sql, (
                data_inicial_obj.strftime('%Y-%m-%d'),
                data_final_obj.strftime('%Y-%m-%d'),
                intervalo
            ))
            print("\nPeríodo de exercício cadastrado com sucesso!")

        except ValueError:
            print("Entrada inválida. Digite um número.")

    def visualizar_periodos(self):
        print("\n=== Períodos de Exercício Cadastrados ===")
        
        sql = """
        SELECT id, start_date, end_date, interval_days 
        FROM fiscal_periods 
        ORDER BY start_date DESC
        """
        periodos = self.db.execute(sql).fetchall()

        if not periodos:
            print("Nenhum período cadastrado.")
            return None

        print("\n{:<5} {:<12} {:<12} {:<15}".format(
            "ID", "Início", "Fim", "Intervalo (dias)"
        ))
        print("-" * 44)

        for p in periodos:
            # Convert dates from YYYY-MM-DD (database) to DD-MM-YYYY (display)
            start_date = datetime.strptime(p[1], '%Y-%m-%d').strftime('%d-%m-%Y')
            end_date = datetime.strptime(p[2], '%Y-%m-%d').strftime('%d-%m-%Y')
            print("{:<5} {:<12} {:<12} {:<15}".format(
                p[0], start_date, end_date, p[3]
            ))

        return periodos

    def excluir_periodo(self):
        periodos = self.visualizar_periodos()
        if not periodos:
            return

        periodo_id = input("\nID do período que deseja excluir (ou 'c' para cancelar): ").lower()
        if periodo_id == 'c':
            return

        try:
            periodo_id = int(periodo_id)
        except ValueError:
            print("ID inválido.")
            return

        confirma = input("Tem certeza que deseja excluir este período? (s/n): ").lower()
        if confirma != 's':
            print("Operação cancelada.")
            return

        sql = "DELETE FROM fiscal_periods WHERE id = ?"
        self.db.execute(sql, (periodo_id,))
        print("Período excluído com sucesso!")

    def get_current_period(self):
        """Returns the most recent fiscal period that includes the current date"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        sql = """
        SELECT id, start_date, end_date, interval_days 
        FROM fiscal_periods 
        WHERE start_date <= ? AND end_date >= ?
        ORDER BY start_date DESC 
        LIMIT 1
        """
        
        return self.db.execute(sql, (current_date, current_date)).fetchone()