# src/interfaces/menu.py
from src.database.connection import Database
from src.services.account_service import AccountService
from src.services.transaction_service import TransactionService
from src.services.template_service import TemplateService
from src.services.fiscal_period_service import FiscalPeriodService
from src.services.report_service import ReportService
from src.services.drp_service import DRPService
from src.utils.backup import import_from_backup, get_backup_files
import os


class MainMenu:
    def __init__(self):
        self.db = Database()
        self.db.connect()
        self.current_menu = 'main'
        self.account_service = AccountService()
        self.transaction_service = TransactionService()
        self.template_service = TemplateService()  
        self.fiscal_period_service = FiscalPeriodService()
        self.drp_service = DRPService()  # Inicialize o DRPService
        self.report_service = ReportService(self.db, self.drp_service)  # Passe o drp_service

    def draw_menu(self, items, title=None):
        print("\n" + "=" * 30)
        if title:
            print(title)
        for idx, item in enumerate(items):
            print(f"{idx + 1}. {item['label']}")
        print("=" * 30)

    def main_menu(self):
        menu_items = [
            {"label": "Cadastros", "action": "cadastros"},
            {"label": "Transações", "action": "transacoes"},
            {"label": "Modelos", "action": "modelos"},
            {"label": "Relatórios", "action": "relatorios"},
            {"label": "Contas a Pagar e a Receber", "action": "contas_pagar_receber"},
            {"label": "Backup/Importação", "action": "backup_importacao"},
            {"label": "Sair", "action": "sair"}
        ]
        self.draw_menu(menu_items)
        return menu_items
    
    def backup_importacao_menu(self):
        """Menu para backup e importação de dados."""
        menu_items = [
            {"label": "Importar Dados de Backup", "action": "importar_backup"},
            {"label": "Voltar", "action": "main"}
        ]
        self.draw_menu(menu_items, "Menu de Backup/Importação")
        return menu_items
    
    def cadastros_menu(self):
        menu_items = [
            {"label": "Categorias", "action": "categorias"},
            {"label": "Contas", "action": "contas"},
            {"label": "Período de Exercício", "action": "periodo_exercicio"},
            {"label": "Voltar", "action": "main"}
        ]
        self.draw_menu(menu_items, "Menu de Cadastros")
        return menu_items
    

    def categorias_menu(self):
        menu_items = [
            {"label": "Cadastrar Categoria", "action": "cadastrar_categoria"},
            {"label": "Visualizar Categorias", "action": "visualizar_categorias"},
            {"label": "Atualizar Categoria", "action": "atualizar_categoria"},
            {"label": "Excluir Categoria", "action": "excluir_categoria"},
            {"label": "Voltar", "action": "cadastros"}
        ]
        self.draw_menu(menu_items, "Categorias")
        return menu_items

    def contas_menu(self):
        menu_items = [
            {"label": "Cadastrar Conta", "action": "cadastrar_conta"},
            {"label": "Visualizar Contas", "action": "visualizar_contas"},
            {"label": "Atualizar Conta", "action": "atualizar_conta"},
            {"label": "Excluir Conta", "action": "excluir_conta"},
            {"label": "Voltar", "action": "cadastros"}
        ]
        self.draw_menu(menu_items, "Contas")
        return menu_items
    
    def periodo_exercicio_menu(self):
        menu_items = [
            {"label": "Cadastrar Período", "action": "cadastrar_periodo"},
            {"label": "Visualizar Períodos", "action": "visualizar_periodos"},
            {"label": "Excluir Período", "action": "excluir_periodo"},
            {"label": "Voltar", "action": "cadastros"}
        ]
        self.draw_menu(menu_items, "Período de Exercício")
        return menu_items

    def template_menu(self):
        menu_items = [
            {"label": "Novo Modelo", "action": "novo_modelo"},
            {"label": "Visualizar Modelos", "action": "visualizar_modelos"},
            {"label": "Editar Modelo", "action": "editar_modelo"},
            {"label": "Excluir Modelo", "action": "excluir_modelo"},
            {"label": "Voltar", "action": "main"}
        ]
        self.draw_menu(menu_items, "Modelos")
        return menu_items

    def transaction_menu(self):
        menu_items = [
            {"label": "Nova Transação", "action": "nova_transacao"},
            {"label": "Nova Transação por Modelo", "action": "executar_modelo"},
            {"label": "Visualizar Transações", "action": "visualizar_transacoes"},
            {"label": "Editar Transação", "action": "editar_transacao"},
            {"label": "Excluir Transação", "action": "excluir_transacao"},
            {"label": "Voltar", "action": "main"}
        ]
        self.draw_menu(menu_items, "Transações")
        return menu_items
    
    def relatorios_menu(self):
        menu_items = [
            {"label": "Demonstração do Resultado do Período (DRP)", "action": "demonstracao_resultado"},
            {"label": "Balanço Patrimonial", "action": "balanco_patrimonial"},  # Ação correta
            {"label": "Índices Financeiros", "action": "indices_financeiros"},
            {"label": "Voltar", "action": "main"}
        ]
        self.draw_menu(menu_items, "Relatórios")
        return menu_items
        
    def contas_pagar_receber_menu(self):
        menu_items = [
            {"label": "Cadastrar nova conta (pagar ou receber)", "action": "cadastrar_conta_pagar_receber"},
            {"label": "Listar contas pendentes", "action": "listar_contas_pendentes"},
            {"label": "Filtrar por vencimento", "action": "filtrar_contas_vencimento"},
            {"label": "Atualizar status (pago/recebido, renegociado, cancelado)", "action": "atualizar_status_conta"},
            {"label": "Gerar relatório de fluxo de caixa futuro", "action": "gerar_relatorio_fluxo_caixa"},
            {"label": "Voltar", "action": "main"}
        ]
        self.draw_menu(menu_items, "Contas a Pagar e a Receber")
        return menu_items
    

    def run(self):
        while True:
            if self.current_menu == 'main':
                menu_items = self.main_menu()
            elif self.current_menu == 'cadastros':
                menu_items = self.cadastros_menu()
            elif self.current_menu == 'categorias':
                menu_items = self.categorias_menu()
            elif self.current_menu == 'contas':
                menu_items = self.contas_menu()
            elif self.current_menu == 'transacoes':
                menu_items = self.transaction_menu()
            elif self.current_menu == 'periodo_exercicio':
                menu_items = self.periodo_exercicio_menu()
            elif self.current_menu == 'modelos':
                menu_items = self.template_menu()
            elif self.current_menu == 'relatorios':
                menu_items = self.relatorios_menu()
            elif self.current_menu == 'contas_pagar_receber':
                menu_items = self.contas_pagar_receber_menu()
            elif self.current_menu == 'backup_importacao':  # Novo menu
                menu_items = self.backup_importacao_menu()
            else:
                print("Menu inválido.")
                break

            try:
                choice = int(input("\nSelecione uma opção: ")) - 1
                if 0 <= choice < len(menu_items):
                    action = menu_items[choice]['action']
                    
                    if action == "sair":
                        print("Saindo...")
                        break
                    elif action in ["main", "cadastros", "categorias", 
                                    "contas", "transacoes", "modelos", 
                                    "periodo_exercicio", "relatorios", 
                                    "backup_importacao"]:
                        self.current_menu = action
                    elif action == "balanco_patrimonial":
                        # Pass the fiscal_period_service argument
                        self.report_service.balanco_patrimonial(self.fiscal_period_service)
                    elif action == "importar_backup":
                        self.importar_backup()
                    else:
                        if hasattr(self.account_service, action):
                            getattr(self.account_service, action)()
                        elif hasattr(self.transaction_service, action):
                            getattr(self.transaction_service, action)()
                        elif hasattr(self.template_service, action):
                            getattr(self.template_service, action)()
                        elif hasattr(self.fiscal_period_service, action):
                            getattr(self.fiscal_period_service, action)()
                        elif hasattr(self.report_service, action):
                            getattr(self.report_service, action)()
                else:
                    print("Opção inválida. Tente novamente.")
            except ValueError:
                print("Entrada inválida. Digite um número.")

    def importar_backup(self):
        """Permite ao usuário importar dados de um backup CSV."""
        print("\n=== Importar Dados de Backup ===")
        
        # Lista os arquivos de backup disponíveis
        backup_files = get_backup_files()
        if not backup_files:
            print("Nenhum arquivo de backup encontrado.")
            return
        
        print("\nArquivos de backup disponíveis:")
        for idx, file in enumerate(backup_files, 1):
            print(f"{idx}. {os.path.basename(file)}")
        
        try:
            choice = int(input("\nSelecione o número do arquivo que deseja importar: ")) - 1
            if 0 <= choice < len(backup_files):
                selected_file = backup_files[choice]
                print(f"\nImportando dados de {os.path.basename(selected_file)}...")
                import_from_backup(selected_file)
            else:
                print("Opção inválida.")
        except ValueError:
            print("Entrada inválida. Digite um número.")