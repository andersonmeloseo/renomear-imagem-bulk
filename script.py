import requests
from bs4 import BeautifulSoup
import paramiko
import os
import pandas as pd
from ftplib import FTP
import re

# Configurações do servidor FTP/SFTP
FTP_HOST = "seu_servidor.com"
FTP_USER = "seu_usuario"
FTP_PASS = "sua_senha"

SFTP_HOST = "seu_servidor.com"
SFTP_PORT = 22
SFTP_USER = "seu_usuario"
SFTP_PASS = "sua_senha"

# Caminho das imagens no servidor
CAMINHO_IMAGENS = "/caminho/das/imagens"

# Nome do arquivo Excel de saída
EXCEL_OUTPUT = "renomeacao_imagens.xlsx"

def obter_imagens_da_pagina(url):
    """Extrai a lista de imagens de uma URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        imagens = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                nome_arquivo = os.path.basename(src)
                imagens.append(nome_arquivo)
        
        return list(set(imagens))  # Remove duplicatas
    except Exception as e:
        print(f"❌ Erro ao acessar a URL: {e}")
        return []

def formatar_nome(nome):
    """Formata o nome da imagem removendo caracteres especiais e adicionando '-'. """
    nome = re.sub(r'[^\w\s-]', '', nome)  # Remove caracteres especiais
    nome = re.sub(r'\s+', '-', nome)  # Substitui espaços por '-'
    return nome.lower()

def conectar_ftp():
    """Conecta ao FTP e retorna o objeto."""
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.cwd(CAMINHO_IMAGENS)
        print(f"✅ Conectado ao FTP: {FTP_HOST}")
        return ftp
    except Exception as e:
        print(f"❌ Erro ao conectar ao FTP: {e}")
        return None

def conectar_sftp():
    """Conecta ao SFTP e retorna o objeto."""
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)
        print(f"✅ Conectado ao SFTP: {SFTP_HOST}")
        return sftp
    except Exception as e:
        print(f"❌ Erro ao conectar ao SFTP: {e}")
        return None

def renomear_arquivos(ftp, arquivos, novos_nomes):
    """Renomeia arquivos no FTP."""
    for idx, (arquivo, novo_nome) in enumerate(zip(arquivos, novos_nomes), start=1):
        novo_arquivo = f"{novo_nome}.jpg"  # Mantém extensão .jpg
        try:
            ftp.rename(arquivo, novo_arquivo)
            print(f"✅ {arquivo} → {novo_arquivo}")
        except Exception as e:
            print(f"❌ Erro ao renomear {arquivo}: {e}")

def renomear_arquivos_sftp(sftp, arquivos, novos_nomes):
    """Renomeia arquivos no SFTP."""
    for idx, (arquivo, novo_nome) in enumerate(zip(arquivos, novos_nomes), start=1):
        novo_arquivo = f"{novo_nome}.jpg"
        caminho_antigo = os.path.join(CAMINHO_IMAGENS, arquivo)
        caminho_novo = os.path.join(CAMINHO_IMAGENS, novo_arquivo)
        try:
            sftp.rename(caminho_antigo, caminho_novo)
            print(f"✅ {arquivo} → {novo_arquivo}")
        except Exception as e:
            print(f"❌ Erro ao renomear {arquivo}: {e}")

def gerar_excel(lista_original, lista_nova):
    """Gera um arquivo Excel contendo a lista de imagens antes e depois da renomeação."""
    data = {
        "Nome Original": lista_original,
        "Nome Renomeado": [f"{novo}.jpg" for novo in lista_nova]
    }
    df = pd.DataFrame(data)
    df.to_excel(EXCEL_OUTPUT, index=False)
    print(f"\n📄 Arquivo Excel '{EXCEL_OUTPUT}' gerado com sucesso!")

def main():
    # Solicita a URL
    url = input("🔗 Digite a URL da página com imagens: ").strip()
    
    # Obtém as imagens da URL
    arquivos_imagens = obter_imagens_da_pagina(url)
    if not arquivos_imagens:
        print("⚠️ Nenhuma imagem encontrada na URL fornecida.")
        return

    print("\n📂 Imagens encontradas:")
    for img in arquivos_imagens:
        print(f" - {img}")

    # Solicita palavras-chave para renomeação
    palavras_chave = input("\n✍️ Digite as palavras-chave separadas por vírgula: ").strip().split(',')

    # Verifica se o número de palavras-chave corresponde ao número de imagens
    if len(palavras_chave) != len(arquivos_imagens):
        print(f"⚠️ Erro: Você forneceu {len(palavras_chave)} palavras, mas há {len(arquivos_imagens)} imagens.")
        return

    # Formata os novos nomes
    novos_nomes = [formatar_nome(palavra.strip()) for palavra in palavras_chave]

    print("\n🔄 Nova nomeação:")
    for antigo, novo in zip(arquivos_imagens, novos_nomes):
        print(f"✅ {antigo} → {novo}.jpg")

    # Pergunta se deseja continuar
    confirmar = input("\n🔄 Deseja renomear os arquivos no servidor? (s/n): ").strip().lower()
    if confirmar != "s":
        print("🚫 Operação cancelada.")
        return

    # Escolhe FTP ou SFTP
    metodo = input("\n🌐 Escolha o método de conexão (FTP/SFTP): ").strip().lower()
    
    if metodo == "ftp":
        ftp = conectar_ftp()
        if ftp:
            renomear_arquivos(ftp, arquivos_imagens, novos_nomes)
            ftp.quit()
    elif metodo == "sftp":
        sftp = conectar_sftp()
        if sftp:
            renomear_arquivos_sftp(sftp, arquivos_imagens, novos_nomes)
            sftp.close()
    else:
        print("❌ Método inválido. Escolha FTP ou SFTP.")

    # Gerar Excel com os nomes originais e renomeados
    gerar_excel(arquivos_imagens, novos_nomes)

    print("\n✅ Renomeação concluída!")

if __name__ == "__main__":
    main()
