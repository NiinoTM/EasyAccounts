# src/services/drp_service.py
from src.database.connection import Database
from src.services.fiscal_period_service import FiscalPeriodService
from datetime import datetime
import os

class DRPService:
    def __init__(self):
        self.db = Database()
        self.db.connect()
        self.fiscal_period_service = FiscalPeriodService()

    def calcular_lucro_periodo(self, periodo_id):
        """
        Calcula o lucro líquido do período com base nas receitas e despesas.
        Retorna o valor do lucro líquido.
        """
        # Seleciona o período fiscal
        periodos = self.fiscal_period_service.visualizar_periodos()
        
        if not periodos:
            print("Nenhum período fiscal cadastrado.")
            return 0  # Retorna 0 se não houver períodos
        
        periodo = next((p for p in periodos if p[0] == periodo_id), None)
        
        if not periodo:
            print("Período não encontrado.")
            return 0  # Retorna 0 se o período não for encontrado
        
        # Consulta para receitas (specific_type: 'entradas' ou 'vendas')
        sql_receitas = """
        SELECT a.id, a.name, 
               COALESCE(SUM(CASE WHEN t.credit_account = a.id THEN t.amount ELSE 0 END), 0) as credit_total,
               COALESCE(SUM(CASE WHEN t.debit_account = a.id THEN t.amount ELSE 0 END), 0) as debit_total
        FROM accounts a
        LEFT JOIN transactions t ON a.id = t.credit_account OR a.id = t.debit_account
        WHERE a.specific_type IN ('entradas', 'vendas')
        AND t.date BETWEEN ? AND ?
        GROUP BY a.id, a.name
        ORDER BY a.name
        """
        
        # Consulta para despesas (specific_type: 'despesas' ou 'compras')
        sql_despesas = """
        SELECT a.id, a.name, 
               COALESCE(SUM(CASE WHEN t.debit_account = a.id THEN t.amount ELSE 0 END), 0) as debit_total,
               COALESCE(SUM(CASE WHEN t.credit_account = a.id THEN t.amount ELSE 0 END), 0) as credit_total
        FROM accounts a
        LEFT JOIN transactions t ON a.id = t.debit_account OR a.id = t.credit_account
        WHERE a.specific_type IN ('despesas', 'compras')
        AND t.date BETWEEN ? AND ?
        GROUP BY a.id, a.name
        ORDER BY a.name
        """
        
        # Executa as consultas
        receitas = self.db.execute(sql_receitas, (periodo[1], periodo[2])).fetchall()
        despesas = self.db.execute(sql_despesas, (periodo[1], periodo[2])).fetchall()
        
        # Calcula os totais
        total_receitas = sum(r[2] - r[3] for r in receitas)  # Receitas: créditos - débitos
        total_despesas = sum(d[2] - d[3] for d in despesas)  # Despesas: débitos - créditos
        
        resultado_liquido = total_receitas - total_despesas
        
        return resultado_liquido  # Retorna o lucro líquido

    def generate_drp_report(self, periodo_id):
        """
        Gera um relatório completo do DRP (Demonstração do Resultado do Período).
        """
        # Seleciona o período fiscal
        periodos = self.fiscal_period_service.visualizar_periodos()
        
        if not periodos:
            print("Nenhum período fiscal cadastrado.")
            return
        
        periodo = next((p for p in periodos if p[0] == periodo_id), None)
        
        if not periodo:
            print("Período não encontrado.")
            return
        
        # Converte as datas para o formato DD-MM-YYYY para exibição
        start_date = datetime.strptime(periodo[1], '%Y-%m-%d').strftime('%d-%m-%Y')
        end_date = datetime.strptime(periodo[2], '%Y-%m-%d').strftime('%d-%m-%Y')
        
        # Calcula o lucro líquido usando o método calcular_lucro_periodo
        resultado_liquido = self.calcular_lucro_periodo(periodo_id)
        
        # Consulta para receitas (specific_type: 'entradas' ou 'vendas')
        sql_receitas = """
        SELECT a.id, a.name, 
               COALESCE(SUM(CASE WHEN t.credit_account = a.id THEN t.amount ELSE 0 END), 0) as credit_total,
               COALESCE(SUM(CASE WHEN t.debit_account = a.id THEN t.amount ELSE 0 END), 0) as debit_total
        FROM accounts a
        LEFT JOIN transactions t ON a.id = t.credit_account OR a.id = t.debit_account
        WHERE a.specific_type IN ('entradas', 'vendas')
        AND t.date BETWEEN ? AND ?
        GROUP BY a.id, a.name
        ORDER BY a.name
        """
        
        # Consulta para despesas (specific_type: 'despesas' ou 'compras')
        sql_despesas = """
        SELECT a.id, a.name, 
               COALESCE(SUM(CASE WHEN t.debit_account = a.id THEN t.amount ELSE 0 END), 0) as debit_total,
               COALESCE(SUM(CASE WHEN t.credit_account = a.id THEN t.amount ELSE 0 END), 0) as credit_total
        FROM accounts a
        LEFT JOIN transactions t ON a.id = t.debit_account OR a.id = t.credit_account
        WHERE a.specific_type IN ('despesas', 'compras')
        AND t.date BETWEEN ? AND ?
        GROUP BY a.id, a.name
        ORDER BY a.name
        """
        
        # Executa as consultas
        receitas = self.db.execute(sql_receitas, (periodo[1], periodo[2])).fetchall()
        despesas = self.db.execute(sql_despesas, (periodo[1], periodo[2])).fetchall()
        
        # Calcula os totais
        total_receitas = sum(r[2] - r[3] for r in receitas)  # Receitas: créditos - débitos
        total_despesas = sum(d[2] - d[3] for d in despesas)  # Despesas: débitos - créditos
        
        # Exibe o relatório
        print("\n" + "=" * 60)
        print(f"DEMONSTRAÇÃO DO RESULTADO DO PERÍODO - {start_date} a {end_date}")
        print("=" * 60)
        
        print("\nRECEITAS")
        print("-" * 60)
        for receita in receitas:
            net_receita = receita[2] - receita[3]  # Créditos - Débitos
            if net_receita > 0:
                print(f"{receita[1]:<40} R$ {net_receita:>13,.2f}")
        print("-" * 60)
        print(f"{'Total de Receitas':<40} R$ {total_receitas:>13,.2f}")
        
        print("\nDESPESAS")
        print("-" * 60)
        for despesa in despesas:
            net_despesa = despesa[2] - despesa[3]  # Débitos - Créditos
            if net_despesa > 0:
                print(f"{despesa[1]:<40} R$ {net_despesa:>13,.2f}")
        print("-" * 60)
        print(f"{'Total de Despesas':<40} R$ {total_despesas:>13,.2f}")
        
        print("\nRESULTADO")
        print("=" * 60)
        print(f"{'Resultado Líquido do Período':<40} R$ {resultado_liquido:>13,.2f}")
        print("=" * 60)
        
        # Calcula e exibe indicadores de desempenho
        if total_receitas > 0:
            margem_liquida = (resultado_liquido / total_receitas) * 100
            print(f"\nMargem Líquida: {margem_liquida:.1f}%")
        
        # Pergunta se o usuário deseja salvar o relatório
        salvar = input("\nDeseja salvar este relatório? (s/n): ").lower()
        if salvar == 's':
            # Define o nome do diretório
            diretorio = r"data\DRP"
            
            # Verifica se o diretório existe, se não, cria o diretório
            if not os.path.exists(diretorio):
                os.makedirs(diretorio)
            
            # Define o nome do arquivo
            nome_arquivo = f"DRP_{start_date}_{end_date}.txt"
            
            # Cria o caminho completo do arquivo
            caminho_completo = os.path.join(diretorio, nome_arquivo)
            
            # Abre o arquivo para escrita
            with open(caminho_completo, 'w') as f:
                f.write(f"DEMONSTRAÇÃO DO RESULTADO DO PERÍODO - {start_date} a {end_date}\n")
                f.write("=" * 60 + "\n\n")
                
                f.write("RECEITAS\n")
                f.write("-" * 60 + "\n")
                for receita in receitas:
                    net_receita = receita[2] - receita[3]
                    if net_receita > 0:
                        f.write(f"{receita[1]:<40} R$ {net_receita:>13,.2f}\n")
                f.write("-" * 60 + "\n")
                f.write(f"{'Total de Receitas':<40} R$ {total_receitas:>13,.2f}\n\n")
                
                f.write("DESPESAS\n")
                f.write("-" * 60 + "\n")
                for despesa in despesas:
                    net_despesa = despesa[2] - despesa[3]
                    if net_despesa > 0:
                        f.write(f"{despesa[1]:<40} R$ {net_despesa:>13,.2f}\n")
                f.write("-" * 60 + "\n")
                f.write(f"{'Total de Despesas':<40} R$ {total_despesas:>13,.2f}\n\n")
                
                f.write("RESULTADO\n")
                f.write("=" * 60 + "\n")
                f.write(f"{'Resultado Líquido do Período':<40} R$ {resultado_liquido:>13,.2f}\n")
                f.write("=" * 60 + "\n")
                
                if total_receitas > 0:
                    f.write(f"\nMargem Líquida: {margem_liquida:.1f}%\n")
            
            print(f"\nRelatório salvo como '{caminho_completo}'")