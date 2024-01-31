import os
import re
import json
from typing import Any

from PyPDF2 import PdfReader
from time import sleep
from datetime import datetime
import pytz

from twocaptcha import TwoCaptcha
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium import webdriver


from env import APIKEY_2CAPTCHA, USUARIO_PJE, SENHA_PJE


class Core:
    """
    Main class to configure Selenium app and enable connections.
    """
    def __init__(self, company_name: str, register_number: str, trt: str, request_type: str):
        self.__company = company_name
        self.__register_number = self.__validate_register(register_number)
        self.__company_path = str(company_name.replace(' ', '_')).lower()
        self.__twocaptcha = TwoCaptcha(APIKEY_2CAPTCHA)
        self.__trt = trt
        self.__request_type = request_type
        self.__browser = self.__generate_browser()


    @staticmethod
    def __validate_register(register_number: str):
        register = re.sub('[^0-9]+', '', register_number)
        if len(register) != 14:
            raise ValueError('The register informed is invalid!')
        return register
    

    def __generate_browser(self):
        path_primary = "/home/panteu/Documentos/Panteu/pandora/pandora/app/banco"
        company_name = self.company_path
        self.folder_company = self.create_folders(path_primary, company_name)
        
        firefox_binary = webdriver.firefox.firefox_binary.FirefoxBinary('/usr/local/bin/firefox')
        options = webdriver.FirefoxOptions()
        #options.add_argument('-headless')
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.useDownloadDir", True)
        options.set_preference("browser.download.dir", self.folder_company)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
        options.set_preference("pdfjs.disabled", True)
        options.set_preference("print.always_print_silent", True)
        return webdriver.Firefox(firefox_binary=firefox_binary, options=options)
    
        
    def create_folders(self, path, company_path):
        folder_company = os.path.join(path, company_path)
        if not os.path.exists(folder_company):
            os.mkdir(folder_company)
        return folder_company

    @property
    def company(self):
        return self.__company
    
    @property
    def company_path(self):
        return self.__company_path

    @property
    def trt(self):
        return self.__trt

    @property
    def twocaptcha(self):
        return self.__twocaptcha

    @property
    def browser(self):
        return self.__browser

    @property
    def register_number(self):
        return self.__register_number

    @property
    def request_type(self):
        return self.__request_type

    def perform_close(self):
        self.browser.close()

    def _perform_create_json_certidao(self, file_name: str, file: dict):
        trt= self.trt
        arquivo = os.path.join(self.folder_company, file_name)
        
        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
                #trt = list(file.keys())[0]
                if trt in current_data:
                    current_data[trt] = file[trt]
                else:
                    current_data.update(file)
        else:
            current_data = file

        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(json.dumps(current_data, indent=4, ensure_ascii=False))


    def _perform_create_json_error(self, file_name: str, file: dict):
        trt= self.trt
        arquivo = os.path.join(self.folder_company, file_name)
        process_number = file[trt]['processos']

        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
                if trt in current_data:
                    if process_number not in current_data[trt]['processos']:
                        current_data[trt]['processos'].append(process_number)
                else:
                    current_data[trt] = {'processos': [process_number]} 
        else:
            current_data = {trt: {'processos': [process_number]}}

        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(json.dumps(current_data, indent=4, ensure_ascii=False))


    def _perform_create_json_dados_processos(self, file_name: str, file: dict):
        arquivo = os.path.join(self.folder_company, file_name)

        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
                process_number = file.get('numero_processo')
                existing_entry = next((entry for entry in current_data if entry.get('numero_processo') == process_number), None)
                if existing_entry:
                    if 'mensagem' in existing_entry:
                        existing_entry.update(file)
                    else:
                        instancia = existing_entry.get('instancia')
                        if instancia == file.get('instancia'):
                            existing_entry.update(file)
                        else:
                            current_data.append(file)
                else:
                    current_data.append(file)

                with open(arquivo, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(current_data, indent=4, ensure_ascii=False))
        else:
            if file_name.startswith(f'dados_processos_{self.trt}.json'):
                with open(arquivo, 'w', encoding='utf-8') as f:
                    f.write(json.dumps([file], indent=4, ensure_ascii=False))

    def store_error_message(self, local, assunto, err, process_number: str = None ):
        error_data = {
            "data_ocorrencia": datetime.now(tz=pytz.timezone('America/Sao_Paulo')).isoformat(),
            "numero_processo": process_number,
            "trt": self.trt,
            "razao_social": self.company,
            "cnpj": self.register_number,
            "tipo_requisicao": "Captura do processo",
            "local": local,
            "assunto": assunto,
            "mensagem": str(err)
        }

        error_data_trt = {self.trt:{
            "data_ocorrencia": datetime.now(tz=pytz.timezone('America/Sao_Paulo')).isoformat(),
            "trt": self.trt,
            "razao_social": self.company,
            "cnpj": self.register_number,
            "tipo_requisicao": "Listagem de processos",
            "local": local,
            "assunto": assunto,
            "mensagem": str(err)
            }
        }
        
        if self.request_type == "listagem_processos":
            self._perform_create_json_certidao(f'Certidoes_{self.company_path}.json', error_data_trt)
        else:
            self._perform_create_json_dados_processos(f'dados_processos_{self.trt}.json', error_data)

    def perform_webdrivewait(self, condition, local, assunto, timeout=30, value: str = None):
        try:
            response = WebDriverWait(self.browser, timeout).until(condition)
        except Exception as err:
            self.store_error_message(
                process_number=value,
                local=local,
                assunto=assunto,
                err=err
            )
            if self.request_type == "captura_processo":
                error_process = {self.trt:{'processos': value}}
                self._perform_create_json_error(f'lista_erros_{self.company_path}.json', error_process)
            raise ValueError(err)
        else:
            return response

    def perform_click_button(self, xpath: str, document: str):
        button = self.perform_webdrivewait(EC.element_to_be_clickable((xpath, document)), "perform_click_button", "Não foi possível inserir os dados.")
        button.click()

    def perform_set_input(self, xpath: str, document: str, value: str):
        document_input = self.perform_webdrivewait(EC.presence_of_element_located((xpath, document)), "perform_set_input", "Não foi possível localizar input.")
        document_input.click()
        document_input.send_keys(value)

    def status_download(self, pasta_download):
        for arquivo in os.listdir(pasta_download):
            while arquivo.endswith(".crdownload") or arquivo.endswith(".download") or arquivo.endswith(".part"):
                if arquivo.endswith(".pdf"):
                    break
            return

    def wait_for_download(self, pasta_download, before_path, tempo_limite):
        condition = lambda driver: os.listdir(pasta_download) != before_path
        self.perform_webdrivewait(condition, "wait_for_download", "Erro ao aguardar o download", tempo_limite)
        self.status_download(pasta_download)

    def perform_clear(self, xpath: str, document: str):
        clear = self.browser.find_element(xpath, document)
        clear.clear()

    def perform_solve_normalcaptcha(
                self, 
                xpath_img: str, 
                document_img: str, 
                xpath_input: str, 
                document_input: str, 
                xpath_button: str, 
                document_button: str,
                time,
                xpath_button_24: str = None, 
                document_button_24: str = None, 
            ):
        for attempt in range(3):
            try:
                captcha_img = self.perform_webdrivewait(EC.visibility_of_element_located((xpath_img, document_img)), f"perform_solve_normalcaptcha", f"Não foi possível passar pelo NormalCaptcha para capturar a certidão no {self.trt}.")
                captcha_img.screenshot(f'captchas/captcha-{self.register_number}.png')
                result = self.twocaptcha.normal(f'captchas/captcha-{self.register_number}.png')
                os.remove(f'captchas/captcha-{self.register_number}.png')
                self.perform_set_input(xpath_input, document_input, result['code'])
                sleep(4)
                before_path = os.listdir(self.folder_company)
                self.perform_click_button(xpath_button, document_button)
                if self.trt == 'trt24':
                    self.perform_click_button(xpath_button_24, document_button_24)
                self.wait_for_download(self.folder_company, before_path, time)
                break
            except Exception as err:
                print(err)
                self.browser.find_element(xpath_input, document_input).clear()

    def perform_exec_script(self, script: str):
        self.browser.execute_script(script)

    def perform_callback(self):
        res = self.browser.execute_script(
            """ 
            return (() => { 
            // eslint-disable-next-line camelcase 
            if (typeof (___grecaptcha_cfg) !== 'undefined') { 
                // eslint-disable-next-line camelcase, no-undef 
                return Object.entries(___grecaptcha_cfg.clients).map(([cid, client]) => { 
                const data = { id: cid, version: cid >= 10000 ? 'V3' : 'V2' }; 
                const objects = Object.entries(client).filter(([_, value]) => value && typeof value === 'object'); 
                objects.forEach(([toplevelKey, toplevel]) => { 
                    const found = Object.entries(toplevel).find(([_, value]) => ( 
                    value && typeof value === 'object' && 'sitekey' in value && 'size' in value 
                    )); 
                    if (typeof toplevel === 'object' && toplevel instanceof HTMLElement && toplevel['tagName'] === 'DIV'){ 
                        data.pageurl = toplevel.baseURI; 
                    } 
                    if (found) { 
                    const [sublevelKey, sublevel] = found; 
                    data.sitekey = sublevel.sitekey; 
                    const callbackKey = data.version === 'V2' ? 'callback' : 'promise-callback'; 
                    const callback = sublevel[callbackKey]; 
                    if (!callback) { 
                        data.callback = null; 
                        data.function = null; 
                    } else { 
                        data.function = callback; 
                        const keys = [cid, toplevelKey, sublevelKey, callbackKey].map((key) => `['${key}']`).join(''); 
                        data.callback = `___grecaptcha_cfg.clients${keys}`; 
                    } 
                    } 
                }); 
                return data; 
                }); 
            } 
            return  ; 
            })()""")

        callback_str = res[0]['callback']
        return callback_str

    def perform_solve_recaptcha(self, sitekey: str, url: str, xpath_emitir: str, document_emitir: str):
        sleep(4)
        result = self.twocaptcha.recaptcha(sitekey=sitekey, url=url)
        self.perform_webdrivewait(
            EC.presence_of_element_located(("id", 'g-recaptcha-response')),
            "perform_solve_recaptcha",
            "Não foi possível passar pelo Recapcha na captura da certidão."
        )
        self.perform_exec_script(f"document.getElementById('g-recaptcha-response').innerHTML = '{result['code']}'")
        if self.trt == 'trt3':
            before_path = os.listdir(self.folder_company)
            self.perform_click_button(xpath_emitir, document_emitir)
            self.wait_for_download(self.folder_company, before_path, 60)
        else:
            callback_str = self.perform_callback()
            self.perform_exec_script(f"{callback_str}('{result['code']}')")
            self.perform_click_button(xpath_emitir, document_emitir)
            self.perform_webdrivewait(
                EC.url_contains(f"https://pje.{self.trt}.jus.br/certidoes/trabalhista/certidao/"),
                "perform_solve_recaptcha",
                "Não foi possível passar pelo Recapcha na captura da certidão.",
                60
            )

    def perform_get_elements_certidao(self, trt: str):
        self.perform_webdrivewait(
            EC.url_contains(f'https://pje.{trt}.jus.br/certidoes/trabalhista/certidao/'),
            "perform_get_elements_certidao",
            "Não foi possível colher numeros de processo."
        )
        sleep(3)
        processos = []
        try:
            encapsulado_shadow = self.browser.find_element("xpath", '/html/body/pje-root/main/pje-visualizador-certidao-trabalhista/section/pje-visualizador-certidao/pje-conteudo-certidao-encapsulado')   
        except:
            paragrafos = self.browser.find_elements(By.CLASS_NAME, "grupo-de-processos-certidao")
            elements = self.browser.find_elements(By.CLASS_NAME, "processos-certidao")
            if elements:
                for index, paragrafo in enumerate(paragrafos):
                    if "BNDT" not in paragrafo.text:
                        processos.extend(numero_processo for processo in elements[index].text.split('\n') 
                                        for numero_processo in processo.split('\n')
                                    )
        else:
            encapsulado = self.browser.execute_script('return arguments[0].shadowRoot', encapsulado_shadow)
            paragrafos = encapsulado.find_elements(By.CLASS_NAME, "grupo-de-processos-certidao")
            elements = encapsulado.find_elements(By.CLASS_NAME, "processos-certidao")
            if elements:
                for index, paragrafo in enumerate(paragrafos):
                    if "BNDT" not in paragrafo.text:
                        processos.extend(numero_processo for processo in elements[index].text.split('\n') 
                                        for numero_processo in processo.split('\n')
                                    )


        certidao = {trt:{'processos': processos}}
        self._perform_create_json_certidao(f'Certidoes_{self.company_path}.json', certidao)
    
    def perform_filter_certidao_pdf(self, trt: str):
        processos = []
        for file in os.listdir(self.folder_company):
            if file.endswith(f'.pdf'):
                file = open(os.path.join(self.folder_company, file), 'rb')
                reader = PdfReader(file)
                numero_paginas = len(reader.pages)
                texto_completo = ''
                for i in range(numero_paginas):
                    pg = reader.pages[i]
                    texto_completo += pg.extract_text()

                padrao = re.findall(r'\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}', texto_completo)
                break
        if padrao:
            certidao = {trt:{'processos': padrao}}
        else:
            certidao = {trt:{'processos': []}}
        self._perform_create_json_certidao(f'Certidoes_{self.company_path}.json', certidao)
        self.perform_clear_downloads_folder()

    def perform_clear_downloads_folder(self):
        for file in os.listdir(self.folder_company):
            if file.endswith('.pdf'):
                os.remove(f"{self.folder_company}/{file}")

    def perform_check_login(self):
        cookies = self.browser.get_cookies()
        access_token_found = False

        for cookie in cookies:
            if cookie['name'] == 'access_token':
                access_token_found = True
                break

        if access_token_found:
            try:
                WebDriverWait(self.browser, 5).until(EC.visibility_of_element_located(('xpath', '//a[@mattooltip="Acesso restrito"]')))       
            except:
                return True
            else:
                try:
                    self.browser.refresh()
                    WebDriverWait(self.browser, 5).until(EC.visibility_of_element_located(('xpath', '//a[@mattooltip="Acesso restrito"]')))
                except:
                    return True
                else: 
                    return False
        else:
            return False 

    def perform_login_pje(self, url_login: str, url_consulta, process_number):
        if not self.perform_check_login():
            self.browser.get(url_login)
            self.browser.find_element("id", "novaSenha") and self.browser.find_element("id", "username")
            self.perform_set_input("id", "username", USUARIO_PJE)
            self.perform_set_input("id", "password", SENHA_PJE)
            self.perform_click_button("id", "btnEntrar")
            self.perform_webdrivewait(
                EC.url_contains(f'https://pje.{self.trt}.jus.br/pjekz/'),
                "perform_login_pje",
                "Não foi possível fazer login.",
                10,
                process_number
            )
            self.browser.get(url_consulta)

    def check_element_visibility(self, xpath):
        try:
            WebDriverWait(self.browser, 5).until(EC.visibility_of_element_located(xpath))
        except Exception as err:
            return str(err)
        else:
            return True

    def check_by_element_visibility(self):
        btn_one = self.check_element_visibility(
            ("xpath", "//button[contains(text(), '2° Grau')]")
        )
        btn_two = self.check_element_visibility(
            ("xpath", "//button[contains(text(), '3° Grau')]")
        )
        if isinstance(btn_one, bool) and isinstance(btn_two, bool):
            return 4
        elif isinstance(btn_one, bool):
            return 3
        return None

    def perform_solve_normalcaptcha_for_process(
            self,
            xpath_img: str,
            document_img: str,
            xpath_input: str,
            document_input: str,
            xpath_button: str,
            document_button: str,
            value: str,
    ):
        for attempt in range(3):
            captcha_img = self.perform_webdrivewait(
                EC.visibility_of_element_located((xpath_img, document_img)),
                "perform_solve_normalcaptcha_for_process",
                "Não foi possível localizar imagem do NormalCaptcha para acessas o processo.",
                30,
                value
            )
            captcha_img.screenshot(f'captchas/captcha{value}.png')
            result = self.twocaptcha.normal(f'captchas/captcha{value}.png')
            os.remove(f'captchas/captcha{value}.png')
            self.perform_set_input(xpath_input, document_input, result['code'])
            self.perform_click_button(xpath_button, document_button)
            sleep(3)
            try:
                wait = WebDriverWait(self.browser, 5)
                confirm =  wait.until(EC.url_contains(f"https://pje.{self.trt}.jus.br/consultaprocessual/detalhe-processo"))
                if confirm:
                    break
            except:
                pass
        else:
            self.perform_webdrivewait(
                EC.url_contains(f"https://pje.{self.trt}.jus.br/consultaprocessual/detalhe-processo/"),
                "perform_solve_normalcaptcha_for_process",
                "Não foi possível passar NormalCaptcha para acessas o processo.",
                5, 
                value)


    def format_db_data(self, process_type: str, process: dict):
        obj = {
                "numero_processo": process.get('numero_processo'),
                "fase": None,
                "vara": None,
                "instancia": None,
                "data_distribuicao": None,
                "data_autuacao": None,
                "valor_causa": None,
                "assunto": None,
                "relator": None,
                "nome_polo_ativo": None,
                "documento_polo_ativo": None,
                "endereco_polo_ativo": None,
                "advogados_polo_ativo": None,
                "cpf_advogados_polo_ativo": None,
                "nome_polo_passivo": None,
                "documento_polo_passivo": None,
                "endereco_polo_passivo": None,
                "advogados_polo_passivo": None,
                "cpf_advogados_polo_passivo":None,
                "nome_terceiros_interessados": None,
                "documento_terceiro_interessados": None,
                "endereco_terceiro_interessados": None,
                "advogados_terceiro_interessados": None,
                "cpf_advogados_polo_terceiro": None,
                "link_pagina" : None,
                "observacao": None
            }
        if process_type == 'Em segredo de justiça':
            obj["observacao"] = "Este processo está correndo em segredo de justiça."
            return obj
        if process_type == 'Nenhum processo encontrado':
            obj["observacao"] = "Não foi possível localiza processos."
            return obj
        return dict(obj, **process)

    def check_process_for_errors(self, process_number: str):
        try:
            button = WebDriverWait(self.browser, 7).until(EC.element_to_be_clickable(("id", "titulo-detalhes")))
            button.click()
        except Exception as err:
            error_element = self.browser.find_element("id", "painel-erro")
            error_message = error_element.find_element("tag name", "span").text
            print(error_message)
            if "segredo de justiça" in error_message:
                data = (self.format_db_data('Em segredo de justiça', {'numero_processo': process_number}))
                self._perform_create_json_dados_processos(f'dados_processos_{self.trt}.json', data)
                return True, False
            return False, False
        else:
            return True, True

    @staticmethod
    def object_constructor(obj: dict, key: str, value: Any) -> dict:
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
                text_elements = [
                    texto.replace('-', ',') 
                    for texto in text_elements]
                
            value = '; '.join(text_elements)
        obj[key] = value
        return obj

    def get_process_elements(self, process_number, instancia):
        processo = self.browser.find_element("xpath", '//*[@id="colunas-dados-processo"]/div[1]/dl')
        ativo = self.browser.find_element(
            "xpath", '/html/body/pje-root/main/pje-detalhe-processo/div[6]/div[2]/div[2]/div[1]'
        )
        advogados_ativo = ativo.find_elements('xpath', ".//small[contains(@class, 'partes-representante')]/i")

        passivo = self.browser.find_element(
            "xpath", '/html/body/pje-root/main/pje-detalhe-processo/div[6]/div[2]/div[2]/div[2]'              
        )
        advogados_passivo = passivo.find_elements('xpath', ".//small[contains(@class, 'partes-representante')]/i")

        terceiros = self.browser.find_element(
            "xpath", "/html/body/pje-root/main/pje-detalhe-processo/div[6]/div[2]/div[2]/div[3]"
        )
        advogados_terceiro = terceiros.find_elements('xpath', ".//small[contains(@class, 'partes-representante')]/i")


        data = self.object_constructor({}, 'numero_processo', self.browser.find_elements("id", "inicio-detalhes-modal"))
        data = self.object_constructor(data, 'fase', self.browser.find_elements("xpath", '//*[@id="cabecalhoVisualizador"]/mat-card-title'))
        data = self.object_constructor(data, 'vara', processo.find_elements("xpath", ".//dt[text()='Órgão julgador:']/following-sibling::dd[1]"))
        data = self.object_constructor(data, 'data_distribuicao', processo.find_elements("xpath", ".//dt[text()='Distribuído:']/following-sibling::dd[1]"))
        data = self.object_constructor(data, 'data_autuacao', processo.find_elements("xpath", ".//dt[text()='Autuado:']/following-sibling::dd[1]"))
        data = self.object_constructor(data, 'valor_causa', processo.find_elements("xpath", ".//dt[text()='Valor da causa:']/following-sibling::dd[1]"))
        data = self.object_constructor(data, 'relator', processo.find_elements("xpath", ".//dt[text()='Relator:']/following-sibling::dd[1]"))
        data = self.object_constructor(data, 'assunto', processo.find_elements("xpath", ".//dt[text()='Assunto(s):']/following-sibling::dd"))
        data = self.object_constructor(data, 'nome_polo_ativo', ativo.find_elements("css selector", 'li.partes-corpo span.nome-parte'))
        data = self.object_constructor(data, 'documento_polo_ativo', ativo.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[3]"))
        data = self.object_constructor(data, 'endereco_polo_ativo', ativo.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[4]") + ativo.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[5]"))
        data = self.object_constructor(data, 'advogados_polo_ativo', ativo.find_elements('xpath', ".//small[contains(@class, 'partes-representante')]/span"))
        data['cpf_advogados_polo_ativo'] = ', '.join([self.browser.execute_script(f'return document.getElementById("{cpf.get_attribute("aria-describedby")}").textContent;')
            for cpf in advogados_ativo]).replace('CPF: ', '')
        data = self.object_constructor(data, 'nome_polo_passivo', passivo.find_elements("css selector", 'li.partes-corpo span.nome-parte'))
        data = self.object_constructor(data, 'documento_polo_passivo', passivo.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[3]"))
        data = self.object_constructor(data, 'endereco_polo_passivo', passivo.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[4]") + passivo.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[5]"))
        data = self.object_constructor(data, 'advogados_polo_passivo', passivo.find_elements('xpath', ".//small[contains(@class, 'partes-representante')]/span"))
        data['cpf_advogados_polo_passivo'] = ', '.join([self.browser.execute_script(f'return document.getElementById("{cpf.get_attribute("aria-describedby")}").textContent;')
            for cpf in advogados_passivo]).replace('CPF: ', '')
        data = self.object_constructor(data, 'nome_terceiros_interessados', terceiros.find_elements("css selector", 'li.partes-corpo span.nome-parte'))
        data = self.object_constructor(data, 'documento_terceiro_interessados', terceiros.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[3]"))
        data = self.object_constructor(data, 'endereco_terceiro_interessados', terceiros.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[4]") + terceiros.find_elements("xpath", ".//li[contains(@class, 'partes-corpo')]//span[5]"))
        data = self.object_constructor(data, 'advogados_terceiro_interessados', terceiros.find_elements('xpath', ".//small[contains(@class, 'partes-representante')]/span"))
        data['cpf_advogados_polo_terceiro'] = ', '.join([self.browser.execute_script(f'return document.getElementById("{cpf.get_attribute("aria-describedby")}").textContent;')
            for cpf in advogados_terceiro]).replace('CPF: ', '')
        data['link_pagina'] = self.browser.current_url
        data['instancia'] = f"{instancia}ªinstancia"
        return data

    def perform_store_process(self, process_number, instancia):
        it_works, has_process = self.check_process_for_errors(process_number)
        if it_works:
            if has_process:
                processo = self.get_process_elements(process_number, instancia)
                return self.format_db_data('Normal', processo)
        return False

    def perform_get_data_by_circuit(self, process_number: str):
        try_again = True
        sleep(3) #TODO MELHORAR VALIDAÇÃO PARA ENCONTRAR URL/ PESQUISAR SOBRE ESPERAR A PAGINA CARREGAR COMPLETAMENTE
        try:
            if self.browser.current_url.startswith(f"https://pje.{self.trt}.jus.br/consultaprocessual/captcha/"):
                self.perform_solve_normalcaptcha_for_process(
                    "id", 'imagemCaptcha', "id", "captchaInput", "id", 'btnEnviar', process_number
                )
                instancia = 1
                processo = self.perform_store_process(process_number, instancia)
                if processo:
                    self._perform_create_json_dados_processos(f'dados_processos_{self.trt}.json', processo)
                    try_again = False
            else:
                value = self.check_by_element_visibility()
                if value is not None:
                    processos = []
                    for index in range(1, value):
                        self.browser.get(f"https://pje.{self.trt}.jus.br/consultaprocessual/captcha/detalhe-processo/{process_number}/{index}")
                        self.perform_solve_normalcaptcha_for_process(
                            "id", 'imagemCaptcha', "id", "captchaInput", "id", 'btnEnviar', process_number
                        )
                        processo = self.perform_store_process(process_number, index)
                        processos.append(processo)
                    if all(processo is not False for processo in processos):
                        for processo in processos:
                            self._perform_create_json_dados_processos(f'dados_processos_{self.trt}.json', processo)
                            try_again = False
                else:
                    processo = self.format_db_data('Nenhum processo encontrado', {'numero_processo': process_number})
                    self._perform_create_json_dados_processos(f'dados_processos_{self.trt}.json', processo)
        except Exception as err:
            try_again = True
            
        return process_number if not try_again else None

    def get_all_process_data(self, trt_config, processes: list):
        processes_ok = []
        for process in processes:
            self.browser.get(trt_config.consultaPublica)
            self.perform_login_pje(trt_config.login_pje, trt_config.consultaPublica, process)
            self.perform_set_input("xpath", '//*[@id="nrProcessoInput"]', process)
            self.perform_click_button("id", 'btnPesquisar')
            process_number = self.perform_get_data_by_circuit(process)
            if process_number:
                processes_ok.append(process_number)
        return processes_ok