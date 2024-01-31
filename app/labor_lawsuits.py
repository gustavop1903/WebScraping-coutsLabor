from munch import Munch
import json
import os
from .core import Core
from env import USUARIO_PJE
from time import sleep

class LaborLawsuits(Core):
    def __init__(self, razao_social: str, cnpj: str, trt: str, tipo_requisicao: str):
        super().__init__(company_name=razao_social, register_number=cnpj, trt=trt, request_type=tipo_requisicao)

    def get_trt_info(self):
        with open('trt_config.json', 'r') as json_file:
            data = json.load(json_file)
        return Munch(data.get(self.trt))
    
    def perform_solve_captcha(self, trt_config):
        if self.trt == 'trt12':
            self.browser.find_element(*trt_config.set_input_two).click()
            self.perform_set_input(*trt_config.set_input_two, self.company)
            self.perform_click_button(*trt_config.click_button_two)
            self.perform_solve_normalcaptcha(*trt_config.solve_captcha)
        elif self.trt == 'trt24':
            sleep(3)
            self.perform_set_input(*trt_config.set_input_two, '446.470.568-56')
            self.perform_click_button(*trt_config.click_button_two)
            self.perform_solve_normalcaptcha(*trt_config.solve_captcha)

        elif self.trt in ['trt7', 'trt8', 'trt10', 'trt21']:
            self.perform_click_button(*trt_config.click_button_two)
        else:
            self.perform_solve_recaptcha(trt_config.sitekey, trt_config.emissao, *trt_config.solve_captcha)

    def perform_get_processes_numbers(self):
        try:
            trt_config = self.get_trt_info()
            self.browser.get(trt_config.emissao)
            self.perform_click_button(*trt_config.click_button)
            self.perform_set_input(*trt_config.set_input, self.register_number)
            self.perform_solve_captcha(trt_config)
            if self.trt not in ['trt12', 'trt3', 'trt24']:
                self.perform_get_elements_certidao(self.trt)
            else:
                self.perform_filter_certidao_pdf(self.trt)
            self.perform_close()
        except Exception as err:
            self.store_error_message(
                local="Erro ao executar perform_get_processes_numbers",
                assunto=f"erro ao colher numeros de processos.",
                err=err
            )
            self.perform_close()
            raise ValueError(f'erro ao colher numeros de processos no {self.trt}')
        
    def perform_get_processes(self, process):
        trt_config = self.get_trt_info()
        self.get_all_process_data(trt_config, process)
        self.perform_close()


    def perform_get_processes_error(self, process):
        arquivo = os.path.join(self.folder_company, f'lista_erros_{self.company_path}.json')
        trt_config = self.get_trt_info()
        processes = self.get_all_process_data(trt_config, process)
        self.perform_close()
        if processes:
            with open(arquivo, 'r') as json_file:
                processes_json = json.load(json_file)
                updated_processes = [process for process in processes_json[self.trt]['processos'] if process not in processes]
                processes_json[self.trt]['processos'] = updated_processes
                with open(arquivo, 'w') as json_file:
                    json.dump(processes_json, json_file)