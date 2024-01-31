from twocaptcha import TwoCaptcha
import re
import json
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium import webdriver
import requests

from env import APIKEY_2CAPTCHA

from selenium import webdriver


class Run():
    def run(self):
        firefox_binary = webdriver.firefox.firefox_binary.FirefoxBinary('/usr/local/bin/firefox')
        options = webdriver.FirefoxOptions()
        #options.add_argument('-headless')
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.useDownloadDir", True)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
        options.set_preference("pdfjs.disabled", True)
        options.set_preference("print.always_print_silent", True)
        self.driver = webdriver.Firefox(firefox_binary=firefox_binary, options = options)


        url = "https://pje.trt1.jus.br/consultaprocessual/detalhe-processo/0100184-73.2022.5.01.0281/1#63e2261"
        self.driver.get(url) 
        sleep(10)
        button = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable(("id", "titulo-detalhes")))
        button.click()
        dados = self.get_process_elements()
        print(dados)
        
            

    @staticmethod
    def object_constructor(obj: dict, key: str, value: any) -> dict:
            print(obj)
            print(value)
            if isinstance(value, list):
                text_elements = [e.text.replace('CPF:', '').replace('CPJ:', '').replace('(ADVOGADO)', '').replace(',', '-').replace('\n', '-').strip() for e in value]
                if key == 'numero_processo':
                    text_elements = [
                        re.findall(
                            r"\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}",
                            texto
                        )[0] for texto in text_elements
                    ]
                if key == 'fase':
                    text_elements = [
                        re.findall(
                            r".*-\s*(.*)",
                            texto
                        )[0] for texto in text_elements
                    ]
                if key == 'valor_causa':
                    text_elements = [texto.replace('-', ',') 
                                     for texto in text_elements]
                value = '; '.join(text_elements)
            obj[key] = value
            return obj

    def get_process_elements(self):
            processo = self.driver.find_element("xpath", '//*[@id="colunas-dados-processo"]/div[1]/dl')
            ativo = self.driver.find_element(
                "xpath", '/html/body/pje-root/main/pje-detalhe-processo/div[6]/div[2]/div[2]/div[1]'
            )
            advogados_ativo = ativo.find_elements('xpath', ".//small[contains(@class, 'partes-representante')]/i")

            passivo = self.driver.find_element(
                "xpath", '/html/body/pje-root/main/pje-detalhe-processo/div[6]/div[2]/div[2]/div[2]'              
            )
            advogados_passivo = passivo.find_elements('xpath', ".//small[contains(@class, 'partes-representante')]/i")

            terceiros = self.driver.find_element(
                "xpath", "/html/body/pje-root/main/pje-detalhe-processo/div[6]/div[2]/div[2]/div[3]"
            )
            data = self.object_constructor({}, 'numero_processo', self.driver.find_elements("id", "inicio-detalhes-modal"))
            data = self.object_constructor(data, 'fase', self.driver.find_elements("xpath", '//*[@id="cabecalhoVisualizador"]/mat-card-title'))
            data = self.object_constructor(data, 'vara', processo.find_elements("xpath", ".//dt[text()='Órgão julgador:']/following-sibling::dd[1]"))
            data = self.object_constructor(data, 'data_distribuicao', processo.find_elements("xpath", ".//dt[text()='Distribuído:']/following-sibling::dd[1]"))
            data = self.object_constructor(data, 'data_autuacao', processo.find_elements("xpath", ".//dt[text()='Autuado:']/following-sibling::dd[1]"))
            data = self.object_constructor(data, 'valor_causa', processo.find_elements("xpath", ".//dt[text()='Valor da causa:']/following-sibling::dd[1]"))
            data = self.object_constructor(data, 'relator', processo.find_elements("xpath", ".//dt[text()='Relator:']/following-sibling::dd[1]"))
            data = self.object_constructor(data, 'assunto', processo.find_elements("xpath", ".//dt[text()='Assunto(s):']/following-sibling::dd"))
            print(data)
            data = self.object_constructor(data, 'nome_polo_ativo', ativo.find_elements("css selector", 'li.partes-corpo span.nome-parte'))
            data = self.object_constructor(data, 'documento_polo_ativo', ativo.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[3]"))
            data = self.object_constructor(data, 'endereco_polo_ativo', ativo.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[4]") + ativo.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[5]"))
            data = self.object_constructor(data, 'advogados_polo_ativo', ativo.find_elements('xpath', ".//small[contains(@class, 'partes-representante')]/span"))
            data['cpf_advogados_polo_ativo'] = ','.join([self.driver.execute_script(f'return document.getElementById("{cpf.get_attribute("aria-describedby")}").textContent;')
            for cpf in advogados_ativo]).replace('CPF: ', '')
            data = self.object_constructor(data, 'nome_polo_passivo', passivo.find_elements("css selector", 'li.partes-corpo span.nome-parte'))
            data = self.object_constructor(data, 'documento_polo_passivo', passivo.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[3]"))
            data = self.object_constructor(data, 'endereco_polo_passivo', passivo.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[4]") + passivo.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[5]"))
            data = self.object_constructor(data, 'advogados_polo_passivo', passivo.find_elements('xpath', ".//small[contains(@class, 'partes-representante')]/span"))
            data['cpf_advogados_polo_passivo'] = ','.join([self.driver.execute_script(f'return document.getElementById("{cpf.get_attribute("aria-describedby")}").textContent;')
            for cpf in advogados_passivo]).replace('CPF: ', '')
            data = self.object_constructor(data, 'nome_terceiros_interessados', terceiros.find_elements("css selector", 'li.partes-corpo span.nome-parte'))
            data = self.object_constructor(data, 'documento_terceiro_interessados', terceiros.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[3]"))
            data = self.object_constructor(data, 'endereco_terceiro_interessados', terceiros.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[4]") + terceiros.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[5]"))
            data = self.object_constructor(data, 'advogados_terceiro_interessados', terceiros.find_elements('xpath', ".//small[contains(@class, 'partes-representante')]/span"))
            data['link_pagina'] = self.driver.current_url
            return data
    
if __name__ == "__main__":
    Run().run()
