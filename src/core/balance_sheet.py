# src/core/balance_sheet.py
from datetime import datetime

class BalanceSheet:
    def __init__(self, db):
        self.db = db

    def calcular_saldos_na_data(self, data):
        """
        Calcula os saldos das contas de ativo, passivo e patrimônio até a data especificada.
        Retorna listas de contas com seus saldos.
        """
        # Consulta todas as contas
        sql_contas = """
        SELECT id, name, type, specific_type, specific_subtype
        FROM accounts
        """
        contas = self.db.execute(sql_contas).fetchall()

        # Inicializa as listas de contas
        ativos_circulantes = []
        ativos_fixos = []
        passivos_circulantes = []
        passivos_nao_circulantes = []
        patrimonio = []

        for conta in contas:
            conta_id, nome, tipo, specific_type, specific_subtype = conta

            # Consulta transações até a data especificada
            sql_transacoes = """
            SELECT COALESCE(SUM(CASE WHEN debit_account = ? THEN amount ELSE 0 END), 0) as total_debito,
                COALESCE(SUM(CASE WHEN credit_account = ? THEN amount ELSE 0 END), 0) as total_credito
            FROM transactions
            WHERE date <= ?
            """
            transacoes = self.db.execute(sql_transacoes, (conta_id, conta_id, data)).fetchone()
            total_debito, total_credito = transacoes

            # Calcula o saldo da conta
            if tipo == 'debito':  # Ativo
                saldo = total_debito - total_credito
            else:  # Passivo ou Patrimônio
                saldo = total_credito - total_debito

            # Cria um dicionário representando a conta com seu saldo
            conta_com_saldo = {
                "id": conta_id,
                "name": nome,
                "type": tipo,
                "specific_type": specific_type,
                "specific_subtype": specific_subtype,
                "balance": saldo
            }

            # Classifica a conta com base no specific_subtype e tipo
            if tipo == 'debito':
                if specific_subtype == 'circulante':
                    ativos_circulantes.append(conta_com_saldo)
                elif specific_subtype == 'fixo':
                    ativos_fixos.append(conta_com_saldo)
            elif tipo == 'credito':
                if specific_subtype == 'circulante':
                    passivos_circulantes.append(conta_com_saldo)
                elif specific_subtype == 'não-circulante':
                    passivos_nao_circulantes.append(conta_com_saldo)
                elif specific_type == 'patrimonio':
                    patrimonio.append(conta_com_saldo)


        return ativos_circulantes, ativos_fixos, passivos_circulantes, passivos_nao_circulantes, patrimonio

    def calcular_totais(self, ativos_circulantes, ativos_fixos, passivos_circulantes, passivos_nao_circulantes, patrimonio, lucro_drp):
        """
        Calcula os totais de ativos, passivos e patrimônio.
        """
        # Soma os saldos das contas
        total_ativos_circulantes = sum(conta["balance"] for conta in ativos_circulantes)
        total_ativos_fixos = sum(conta["balance"] for conta in ativos_fixos)
        total_passivos_circulantes = sum(conta["balance"] for conta in passivos_circulantes)
        total_passivos_nao_circulantes = sum(conta["balance"] for conta in passivos_nao_circulantes)
        total_patrimonio = sum(conta["balance"] for conta in patrimonio)

        # Calcula os totais
        total_ativos = total_ativos_circulantes + total_ativos_fixos
        total_passivos_patrimonio = total_passivos_circulantes + total_passivos_nao_circulantes + total_patrimonio + lucro_drp

        return total_ativos, total_passivos_patrimonio