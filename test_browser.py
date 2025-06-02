from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
import sys

def test_nova_ordem(cliente_id=2, base_url="http://localhost:8000", username="admin", password="admin", headless=False):
    """
    Testa o carregamento de equipamentos na página de nova ordem usando Selenium.
    """
    # Configurar o driver
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)  # espera implícita de 10 segundos
    
    try:
        # Acessar a página de login
        print(f"Acessando: {base_url}/login/")
        driver.get(f"{base_url}/login/")
        
        # Preencher o formulário de login
        print(f"Fazendo login como: {username}")
        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # Esperar carregar a página após o login
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "main-content"))
        )
        
        # Acessar a página de nova ordem
        print("Acessando página de nova ordem...")
        driver.get(f"{base_url}/ordens/nova/")
        
        # Esperar carregar a página
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "cliente"))
        )
        
        # Selecionar o cliente pelo ID (usando JavaScript para garantir que o evento change seja disparado)
        print(f"Selecionando cliente ID: {cliente_id}")
        driver.execute_script(f"$('#cliente').val({cliente_id}); $('#cliente').trigger('change');")
        
        # Esperar até que o select de equipamentos tenha opções além do padrão
        time.sleep(2)  # Dar tempo para o AJAX completar
        
        # Pegar o conteúdo do console
        logs = driver.execute_script("return console.logs")
        print("Logs do console:")
        print(logs)
        
        # Verificar o conteúdo do select de equipamentos
        equipamentos_select = driver.find_element(By.ID, "equipamento")
        options = equipamentos_select.find_elements(By.TAG_NAME, "option")
        
        print(f"Opções de equipamentos encontradas: {len(options)}")
        for option in options:
            print(f"  - {option.get_attribute('value')}: {option.text}")
        
        # Capturar o valor do elemento select
        selected_value = driver.execute_script("return $('#equipamento').val();")
        print(f"Valor selecionado: {selected_value}")
        
        # Tirar screenshot para registro
        driver.save_screenshot("test_nova_ordem.png")
        print("Screenshot salvo como test_nova_ordem.png")
        
        return True
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        driver.save_screenshot("error.png")
        print("Screenshot de erro salvo como error.png")
        return False
        
    finally:
        # Fechar o navegador
        driver.quit()

if __name__ == "__main__":
    cliente_id = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    test_nova_ordem(cliente_id) 