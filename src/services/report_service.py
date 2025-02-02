# src/services/report_service.py
from src.services.drp_service import DRPService
from src.services.balance_sheet_service import BalanceSheetService
from datetime import datetime
from rich.console import Console

class ReportService:
    def __init__(self, db, drp_service):  # Adicione drp_service como argumento
        self.db = db
        self.drp_service = drp_service  # Atribua o drp_service
        self.balance_sheet_service = BalanceSheetService(db)

    def menu_relatorios(self):
        while True:
            print("\n=== Menu de Relatórios ===")
            print("1. Demonstração do Resultado do Período (DRP)")
            print("2. Balanço Patrimonial")
            print("3. Índices Financeiros")
            print("4. Voltar")
            
            try:
                opcao = int(input("\nEscolha uma opção: "))
                if opcao == 1:
                    self.demonstracao_resultado()
                elif opcao == 2:
                    self.balanco_patrimonial(self.drp_service.fiscal_period_service)  # Passar o fiscal_period_service
                elif opcao == 3:
                    print("\nFuncionalidade em desenvolvimento.")
                elif opcao == 4:
                    break
                else:
                    print("Opção inválida!")
            except ValueError:
                print("Por favor, digite um número válido!")

    def demonstracao_resultado(self):
        print("\n=== Demonstração do Resultado do Período ===")
        
        # Select fiscal period
        print("\nSelecione o período para o relatório:")
        periodos = self.drp_service.fiscal_period_service.visualizar_periodos()
        
        if not periodos:
            print("Nenhum período fiscal cadastrado.")
            return
            
        try:
            periodo_id = int(input("\nDigite o ID do período desejado: "))
            self.drp_service.generate_drp_report(periodo_id)
        except ValueError:
            print("Entrada inválida. Digite um número válido.")

    def balanco_patrimonial(self, fiscal_period_service):
        console = Console()

        # Listar períodos cadastrados (já exibido pelo visualizar_periodos)
        periodos = fiscal_period_service.visualizar_periodos()
        if not periodos:
            return  # A mensagem de erro já foi exibida pelo visualizar_periodos

        # Solicitar escolha do período
        try:
            periodo_id = int(input("\nEscolha o ID do período de exercício: "))
        except ValueError:
            console.print("[bold red]ID inválido. Insira um número inteiro.[/bold red]")
            return

        # Verificar se o período existe
        periodo_escolhido = next((p for p in periodos if p[0] == periodo_id), None)
        if not periodo_escolhido:
            console.print("[bold red]Período não encontrado.[/bold red]")
            return

        # Data final do período escolhido
        data_final_periodo = periodo_escolhido[2]  # Já está no formato 'YYYY-MM-DD'

        # Calcular o lucro da DRP para o período escolhido
        try:
            lucro_drp = self.drp_service.calcular_lucro_periodo(periodo_id)
        except Exception as e:
            console.print(f"[bold red]Erro ao calcular o lucro da DRP: {e}[/bold red]")
            return

        # Gerar o Balanço Patrimonial
        self.balance_sheet_service.gerar_balanco_patrimonial(data_final_periodo, lucro_drp)