# src/services/fiscal_period_service.py
from datetime import datetime, timedelta
from src.database.connection import Database
from src.utils.validators import validate_and_convert_date

class FiscalPeriodService:
    def __init__(self):
        self.db = Database()
        self.db.connect()

    def cadastrar_periodo(self):
        print("\n=== Cadastrar Período de Exercício ===")
        
        # Get initial date in any format
        while True:
            data_inicial = input("Data inicial (qualquer formato com dia, mês e ano): ").strip()
            formatted_date = validate_and_convert_date(data_inicial, "%d-%m-%Y")
            if formatted_date:
                print(f"Data convertida: {formatted_date}")
                break
            print("Data inválida. Certifique-se de incluir dia, mês e ano.")

        # Get interval type
        print("\nTipo de intervalo:")
        print("1. Mensal (1 mês)")
        print("2. Trimestral (3 meses)")
        print("3. Semestral (6 meses)")
        print("4. Anual (12 meses)")
        print("5. Personalizado")

        while True:
            try:
                opcao = input("\nEscolha uma opção: ").strip()
                opcao = int(opcao)  # Convert input to integer
                if 1 <= opcao <= 5:  # Check if the option is within the valid range
                    break
                else:
                    print("Opção inválida. Escolha um número entre 1 e 5.")
            except ValueError:
                print("Entrada inválida. Digite um número.")

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
            intervalos = {1: 1, 2: 3, 3: 6, 4: 12}
            intervalo = intervalos.get(opcao)

        # Calculate end date by adding months or years
        data_inicial_obj = datetime.strptime(formatted_date, '%d-%m-%Y')
        if opcao != 5:
            # Calculate the new month and year
            new_month = data_inicial_obj.month + intervalo
            new_year = data_inicial_obj.year
            if new_month > 12:
                new_year += (new_month - 1) // 12
                new_month = (new_month - 1) % 12 + 1
            data_final_obj = data_inicial_obj.replace(year=new_year, month=new_month)
        else:
            # For custom interval, add days as before
            data_final_obj = data_inicial_obj + timedelta(days=intervalo)

        data_final = data_final_obj.strftime('%d-%m-%Y')

        # Show summary in DD-MM-YYYY format
        print("\nResumo do período:")
        print(f"Data inicial: {formatted_date}")
        print(f"Data final: {data_final}")
        print(f"Intervalo: {intervalo} {'meses' if opcao != 5 else 'dias'}")

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
            "ID", "Início", "Fim", "Intervalo (meses)"
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