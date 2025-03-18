import os
import gdown
import duckdb
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime

# Obs: importação NÃO necessária, a tipagem será utilizada apenas para 1 exemplo
from duckdb import DuckDBPyRelation
from pandas import DataFrame

load_dotenv()

# Conecta com o banco "duck.db" / cria um banco caso não exista.
def conectar_banco():
    return duckdb.connect(database="duckdb.db", read_only=False)

# Cria uma tabela no banco "duckdb.db" caso ela não exista
def inicializar_tabela(con):
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS historico_arquivos(
            nome_arquivo VARCHAR,
            horario_processamento TIMESTAMP
        )
        """
    )

# Registra um novo arquivo no banco com horário atual
def registrar_arquivo(con, nome_arquivo):
    con.execute(
        """
        INSERT INTO historico_arquivos (nome_arquivo, horario_processamento) VALUES (?, ?)
        """, (nome_arquivo, datetime.now())
    )

# Retorna um set com o nome dos arquivos já processados
def arquivos_processados(con):
    return set(row[0] for row in con.execute("SELECT nome_arquivo FROM historico_arquivos").fetchall())


# Função para baixar arquivos do Drive
def baixar_arquivos_google_drive(url_pasta, dir_local):
    os.makedirs(dir_local, exist_ok=True)
    gdown.download_folder(url_pasta, output=dir_local, quiet=False, use_cookies=False)

# Função para listar arquivos CSV do diretório
def listar_arquivos_csv(diretorio):
    arquivos_csv = []
    todos_arquivos = os.listdir(diretorio)
    for arquivo in todos_arquivos:
        if arquivo.endswith(".csv"):
            caminho_completo = os.path.join(diretorio, arquivo)
            arquivos_csv.append(caminho_completo)
    return arquivos_csv

# Função para ler CSV
def ler_csv(caminho_arquivo):
    df = duckdb.read_csv(caminho_arquivo)
    return df

# Transformação df
# Obs: Estamos tipando esse exemplo (não necessário)
# Obs2: aplicamos o ".df()" no final para converter em dataframe do pandas
def transformar(df: DuckDBPyRelation) -> DataFrame:
    df_transformado = duckdb.sql("SELECT *, quantidade * valor as total_vendas FROM df").df()
    return df_transformado

def salvar_postegres(df_duckdb, tabela):
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    #Salvar df no banco PostegreSQL
    df_duckdb.to_sql(tabela, con=engine, if_exists='append', index=False)

if __name__ == '__main__':
    url_pasta = 'https://drive.google.com/drive/folders/1Inda8n1yz05fnVzcRBtNOWGMxABQR5Wh?'
    dir_local = r'./pasta_gdown'
    # baixar_arquivos_google_drive(url_pasta, dir_local)
    lista_de_arquivos = listar_arquivos_csv(dir_local)
    con = conectar_banco()
    inicializar_tabela(con)
    processados = arquivos_processados(con)

    
    for caminho_arquivo in lista_de_arquivos:
        nome_arquivo = os.path.basename(caminho_arquivo)
        if nome_arquivo not in processados:
            df_duck = ler_csv(caminho_arquivo)
            df_duck_transformado = transformar(df_duck)
            salvar_postegres(df_duck_transformado, "vendas_calculado")
            registrar_arquivo(con, nome_arquivo)
            print(f"Arquivo {nome_arquivo} processado e salvo.")
        else:
            print(f"Arquivo {nome_arquivo} já foi processado anteriormente.")