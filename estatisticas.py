from api_client import buscar_dados_api
from excel_manager import salvar_excel, ler_excel

def obter_estatisticas():
# 1. Tenta API
dados_api = buscar_dados_api()

if dados_api:
    # Atualiza Excel e usa API como fonte oficial
    salvar_excel(dados_api)
    return {
        "fonte": "api",
        "dados": dados_api
    }

# 2. Fallback → Excel
dados_excel = ler_excel()

if dados_excel:
    return {
        "fonte": "excel",
        "dados": dados_excel
    }

# 3. Se tudo falhar
return {
    "erro": "Nenhuma fonte de dados disponível."
}
