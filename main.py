import sqlite3
import random
from datetime import datetime
from fpdf import FPDF
def conectar():
    return sqlite3.connect('gestao_epi_sesmt.db')
def cadastrar_epi(nome, ca, valor):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO epis (nome, ca, valor) VALUES (?,?,?)", (nome, ca, valor))
    conn.commit()
    conn.close()
    print(f"✅ EPI {nome} (CA {ca}) cadastrado!")
def cadastrar_funcionario(nome, mat, setor, func, zap):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO funcionarios (nome, matricula, setor, funcao, whatsapp) VALUES (?,?,?,?,?)", 
                       (nome, mat, setor, func, zap))
        conn.commit()
        print(f"✅ Colaborador {nome} cadastrado com sucesso!")
    except:
        print("❌ Erro: Matrícula já existe no sistema.")
    conn.close()
def realizar_entrega(matricula, ca_epi):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, whatsapp FROM funcionarios WHERE matricula=?", (matricula,))
    func = cursor.fetchone()
    cursor.execute("SELECT id, nome FROM epis WHERE ca=?", (ca_epi,))
    epi = cursor.fetchone()
    if not func or not epi:
        print("❌ Erro: Funcionário ou EPI não encontrado!")
        return
    token = str(random.randint(100000, 999999))
    print(f"\n--- SESMT HUC/ISGH - ENVIANDO TOKEN PARA: {func[1]} ---")
    print(f"MENSAGEM: Seu código de confirmação de recebimento de EPI é: {token}")
    cursor.execute("INSERT INTO entregas (id_funcionario, id_epi, token_validacao) VALUES (?,?,?)", (func[0], epi[0], token))
    id_entrega = cursor.lastrowid
    conn.commit()
    confirmacao = input("\nDigite o token de confirmação recebido pelo colaborador: ")
    if confirmacao == token:
        cursor.execute("UPDATE entregas SET status='ENTREGUE' WHERE id=?", (id_entrega,))
        conn.commit()
        print("✅ SUCESSO: Entrega confirmada juridicamente pelo SESMT.")
    else:
        print("❌ ERRO: Token inválido. Processo cancelada.")
    conn.close()
def gerar_pdf(matricula):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT f.nome, f.setor, e.data_solicitacao, ep.nome, ep.ca, ep.valor, f.funcao
        FROM entregas e
        JOIN funcionarios f ON e.id_funcionario = f.id
        JOIN epis ep ON e.id_epi = ep.id
        WHERE f.matricula = ? AND e.status = 'ENTREGUE'
    ''', (matricula,))
    dados = cursor.fetchall()
    if not dados:
        print("Nenhuma entrega confirmada para este colaborador.")
        return
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "HOSPITAL UNIVERSITARIO DO CEARA - HUC / ISGH", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "SESMT - SISTEMA DE ENTREGA DE EPI DIGITAL", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 7, f"Colaborador: {dados[0][0]} | Matricula: {matricula}", ln=True)
    pdf.cell(200, 7, f"Cargo: {dados[0][6]} | Setor: {dados[0][1]}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(35, 8, "Data", 1); pdf.cell(85, 8, "Equipamento", 1); pdf.cell(30, 8, "C.A.", 1); pdf.cell(30, 8, "Valor", 1, ln=True)
    pdf.set_font("Arial", size=9)
    total = 0
    for d in dados:
        pdf.cell(35, 8, str(d[2])[:10], 1)
        pdf.cell(85, 8, str(d[3]), 1)
        pdf.cell(30, 8, str(d[4]), 1)
        pdf.cell(30, 8, f"R$ {d[5]:.2f}", 1, ln=True)
        total += d[5]
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(200, 10, f"CUSTO TOTAL DE CONSUMO: R$ {total:.2f}", ln=True)
    nome_arq = f"Ficha_SESMT_HUC_{matricula}.pdf"
    pdf.output(nome_arq)
    print(f"📄 Relatório gerado com sucesso: {nome_arq}")
    conn.close()
if __name__ == "__main__":
    while True:
        print("\n" + "="*45)
        print("   SISTEMA DE ENTREGA DE EPI - SESMT - HUC   ")
        print("="*45)
        print("1. Cadastrar Colaborador")
        print("2. Cadastrar Novo EPI")
        print("3. Entrega com Token (Assinatura Digital)")
        print("4. Gerar Relatório de Consumo (PDF)")
        print("0. Sair")
        opcao = input("\nSelecione uma opção: ")
        if opcao == "1":
            cadastrar_funcionario(input("Nome: "), input("Matrícula: "), input("Setor: "), input("Função: "), input("WhatsApp: "))
        elif opcao == "2":
            cadastrar_epi(input("EPI: "), input("C.A.: "), float(input("Preço Unitário: ")))
        elif opcao == "3":
            realizar_entrega(input("Matrícula: "), input("C.A. do EPI: "))
        elif opcao == "4":
            gerar_pdf(input("Matrícula: "))
        elif opcao == "0": break
