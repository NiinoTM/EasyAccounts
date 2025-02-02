from tabulate import tabulate
from src.core.balance_sheet import BalanceSheet
import os
from datetime import datetime

class BalanceSheetService:
    def __init__(self, db):
        self.db = db
        self.balance_sheet = BalanceSheet(db)

    def exibir_balanco_patrimonial(self, ativos_circulantes, ativos_fixos, passivos_circulantes, passivos_nao_circulantes, patrimonio, lucro_drp):
        """
        Exibe o balanço patrimonial usando a biblioteca tabulate de forma alinhada,
        inserindo uma linha em branco após cada total e separando a seção de patrimônio.
        """
        # Calcula os totais necessários
        total_ativos_circulantes = sum(conta['balance'] for conta in ativos_circulantes)
        total_ativos_fixos = sum(conta['balance'] for conta in ativos_fixos)
        total_passivos_circulantes = sum(conta['balance'] for conta in passivos_circulantes)
        total_passivos_nao_circulantes = sum(conta['balance'] for conta in passivos_nao_circulantes)
        total_patrimonio_liquido = sum(conta['balance'] for conta in patrimonio)
        total_patrimonio = total_patrimonio_liquido + lucro_drp
        total_passivos_e_patrimonio = total_passivos_circulantes + total_passivos_nao_circulantes + total_patrimonio
        total_ativos = total_ativos_circulantes + total_ativos_fixos

        # Monta a seção de Ativos, inserindo uma linha em branco após cada total
        ativos_section = (
            [["Ativos Circulantes", ""]]
            + [[conta["name"], f"R$ {conta['balance']:,.2f}"] for conta in ativos_circulantes]
            + [
                ["Total Ativos Circulantes", f"R$ {total_ativos_circulantes:,.2f}"],
                ["", ""],
                ["Ativos Fixos", ""]
            ]
            + [[conta["name"], f"R$ {conta['balance']:,.2f}"] for conta in ativos_fixos]
            + [
                ["Total Ativos Fixos", f"R$ {total_ativos_fixos:,.2f}"],
                ["", ""]
            ]
        )

        # Monta a seção de Passivos e Patrimônio
        passivos_section = (
            [["Passivos Circulantes", ""]]
            + [[conta["name"], f"R$ {conta['balance']:,.2f}"] for conta in passivos_circulantes]
            + [
                ["Total Passivos Circulantes", f"R$ {total_passivos_circulantes:,.2f}"],
                ["", ""],
                ["Passivos Não Circulantes", ""]
            ]
            + [[conta["name"], f"R$ {conta['balance']:,.2f}"] for conta in passivos_nao_circulantes]
            + [
                ["Total Passivos Não Circulantes", f"R$ {total_passivos_nao_circulantes:,.2f}"],
                ["", ""],
                ["Patrimônio Líquido", f"R$ {total_patrimonio_liquido:,.2f}"],
                ["Lucro da DRP", f"R$ {lucro_drp:,.2f}"],
                ["Total Patrimônio", f"R$ {total_patrimonio:,.2f}"],
                ["", ""]
            ]
        )

        # Determina o número máximo de linhas entre as seções
        max_rows = max(len(ativos_section), len(passivos_section))

        # Preenche as seções com linhas vazias para que tenham o mesmo número de linhas
        while len(ativos_section) < max_rows:
            ativos_section.append(["", ""])
        while len(passivos_section) < max_rows:
            passivos_section.append(["", ""])

        # Combina as seções lado a lado
        table_data = []
        for ativo, passivo in zip(ativos_section, passivos_section):
            table_data.append([ativo[0], ativo[1], passivo[0], passivo[1]])
        
        # Adiciona a linha final com os totais
        table_data.append(["Total Ativos", f"R$ {total_ativos:,.2f}", "Total Passivos e Patrimônio", f"R$ {total_passivos_e_patrimonio:,.2f}"])

        # Exibe a tabela formatada
        print(tabulate(table_data, headers=["ATIVOS", "VALOR", "PASSIVOS E PATRIMÔNIO", "VALOR"], tablefmt="pretty"))

    def exportar_balanco_patrimonial(self, data, table_data):
        """
        Exports the balance sheet to a .txt file.
        """
        directory = r'data\Balanço Patrimonial'
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Ensure `data` is a datetime object
        if isinstance(data, str):
            data = datetime.strptime(data, "%Y-%m-%d")  # Adjust format as needed

        end_period = data.strftime("%d.%m.%Y")
        file_name = f"Balanco Patrimonial - {end_period}.txt"
        file_path = os.path.join(directory, file_name)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(tabulate(table_data, headers=["ATIVOS", "VALOR", "PASSIVOS E PATRIMÔNIO", "VALOR"], tablefmt="pretty"))
        
        print(f"Balanço patrimonial exportado para {file_path}")

    def gerar_balanco_patrimonial(self, data, lucro_drp):
        """
        Gera o Balanço Patrimonial para a data especificada.
        """
        ativos_circulantes, ativos_fixos, passivos_circulantes, passivos_nao_circulantes, patrimonio = self.balance_sheet.calcular_saldos_na_data(data)
        
        # Debug: Print the data being passed
        print("Ativos Circulantes:", ativos_circulantes)
        print("Ativos Fixos:", ativos_fixos)
        print("Passivos Circulantes:", passivos_circulantes)
        print("Passivos Não Circulantes:", passivos_nao_circulantes)
        print("Patrimônio:", patrimonio)
        
        self.exibir_balanco_patrimonial(ativos_circulantes, ativos_fixos, passivos_circulantes, passivos_nao_circulantes, patrimonio, lucro_drp)

        # Ask if the user wants to export the balance sheet
        exportar = input("Deseja exportar o balanço patrimonial? (s/n): ").strip().lower()
        if exportar == 's':
            # Prepare the table data for exporting
            table_data = self.prepare_table_data(ativos_circulantes, ativos_fixos, passivos_circulantes, passivos_nao_circulantes, patrimonio, lucro_drp)
            self.exportar_balanco_patrimonial(data, table_data)

    def prepare_table_data(self, ativos_circulantes, ativos_fixos, passivos_circulantes, passivos_nao_circulantes, patrimonio, lucro_drp):
        """
        Prepares the table data for exporting.
        """
        # Calcula os totais necessários
        total_ativos_circulantes = sum(conta['balance'] for conta in ativos_circulantes)
        total_ativos_fixos = sum(conta['balance'] for conta in ativos_fixos)
        total_passivos_circulantes = sum(conta['balance'] for conta in passivos_circulantes)
        total_passivos_nao_circulantes = sum(conta['balance'] for conta in passivos_nao_circulantes)
        total_patrimonio_liquido = sum(conta['balance'] for conta in patrimonio)
        total_patrimonio = total_patrimonio_liquido + lucro_drp
        total_passivos_e_patrimonio = total_passivos_circulantes + total_passivos_nao_circulantes + total_patrimonio
        total_ativos = total_ativos_circulantes + total_ativos_fixos

        # Monta a seção de Ativos, inserindo uma linha em branco após cada total
        ativos_section = (
            [["Ativos Circulantes", ""]]
            + [[conta["name"], f"R$ {conta['balance']:,.2f}"] for conta in ativos_circulantes]
            + [
                ["Total Ativos Circulantes", f"R$ {total_ativos_circulantes:,.2f}"],
                ["", ""],
                ["Ativos Fixos", ""]
            ]
            + [[conta["name"], f"R$ {conta['balance']:,.2f}"] for conta in ativos_fixos]
            + [
                ["Total Ativos Fixos", f"R$ {total_ativos_fixos:,.2f}"],
                ["", ""]
            ]
        )

        # Monta a seção de Passivos e Patrimônio
        passivos_section = (
            [["Passivos Circulantes", ""]]
            + [[conta["name"], f"R$ {conta['balance']:,.2f}"] for conta in passivos_circulantes]
            + [
                ["Total Passivos Circulantes", f"R$ {total_passivos_circulantes:,.2f}"],
                ["", ""],
                ["Passivos Não Circulantes", ""]
            ]
            + [[conta["name"], f"R$ {conta['balance']:,.2f}"] for conta in passivos_nao_circulantes]
            + [
                ["Total Passivos Não Circulantes", f"R$ {total_passivos_nao_circulantes:,.2f}"],
                ["", ""],
                ["Patrimônio Líquido", f"R$ {total_patrimonio_liquido:,.2f}"],
                ["Lucro da DRP", f"R$ {lucro_drp:,.2f}"],
                ["Total Patrimônio", f"R$ {total_patrimonio:,.2f}"],
                ["", ""]
            ]
        )

        # Determina o número máximo de linhas entre as seções
        max_rows = max(len(ativos_section), len(passivos_section))

        # Preenche as seções com linhas vazias para que tenham o mesmo número de linhas
        while len(ativos_section) < max_rows:
            ativos_section.append(["", ""])
        while len(passivos_section) < max_rows:
            passivos_section.append(["", ""])

        # Combina as seções lado a lado
        table_data = []
        for ativo, passivo in zip(ativos_section, passivos_section):
            table_data.append([ativo[0], ativo[1], passivo[0], passivo[1]])
        
        # Adiciona a linha final com os totais
        table_data.append(["Total Ativos", f"R$ {total_ativos:,.2f}", "Total Passivos e Patrimônio", f"R$ {total_passivos_e_patrimonio:,.2f}"])

        return table_data
