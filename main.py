from app.labor_lawsuits import LaborLawsuits
import concurrent.futures
import argparse
import os
import json
import queue



def worker(trt, obj):
    try:
        result = LaborLawsuits(
            tipo_requisicao="listagem_processos", trt=trt, **obj
        ).perform_get_processes_numbers()
        return result
    except Exception as err:
        return f'Erro: {err}'

def start_certidao(*args, **kwargs):
    obj = args[0]

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        result_queue = queue.Queue()
        futures = []
        
        for i in range(24, 25):
            trt = f'trt{i}'
            future = executor.submit(worker, trt, obj)
            futures.append(future)
            
    for future in concurrent.futures.as_completed(futures):
        try:
            result = future.result()
        except Exception as e:
            print(f'Erro: {e}')
        else:
            result_queue.put(result)
                
    while not result_queue.empty():
        result = result_queue.get()
        print(result)

def worker_process(trt, processos, obj):
    try:
        result = LaborLawsuits(
            tipo_requisicao="captura_processo", trt=trt, **obj
        ).perform_get_processes(processos)
        return result
    except Exception as err:
        return f'Erro: {err}'

def convert_name(obj: dict):
    company = obj["razao_social"]
    name = str(company.replace(' ', '_')).lower()
    folder = f'app/banco/{name}'
    return folder, name

def start_processos(obj: dict):
    folder, name = convert_name(obj)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        result_queue = queue.Queue()
        futures=[]
        arquivo = os.path.join(folder, f'Certidoes_{name}.json')
        with open(arquivo, 'r', encoding='utf-8') as f:
            certidao = json.load(f)
            for trt, data in certidao.items():
                if "processos" in data:
                    processos = data["processos"]
                    future = executor.submit(worker_process, trt, processos, obj)
                    futures.append(future)

    for future in concurrent.futures.as_completed(futures):
        try:
            result = future.result()
        except Exception as e:
            print(f'Erro: {e}')

def start_processos_error(obj: dict):
    folder, name = convert_name(obj)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        arquivo = os.path.join(folder, f'lista_erros_{name}.json')
        with open(arquivo, 'r', encoding='utf-8') as f:
            certidao = json.load(f)
            for trt, data in certidao.items():
                processos = data["processos"]
                try:
                    processes = LaborLawsuits(tipo_requisicao="captura_processo", trt=trt, **obj)
                    futures.append(executor.submit(processes.perform_get_processes_error, processos))
                except Exception as err:
                    print(err)
    for future in concurrent.futures.as_completed(futures):
        try:
            result = future.result()
        except Exception as e:
            print(f'Erro: {e}')

def start_trt(obj:dict):
    folder, name = convert_name(obj)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        result_queue = queue.Queue()
        futures=[]
        arquivo = os.path.join(folder, f'Certidoes_{name}.json')
        with open(arquivo, 'r', encoding='utf-8') as f:
            certidao = json.load(f)
            for trt, data in certidao.items():
                if trt in ['trt5']:
                    if "processos" in data:
                        processos = data["processos"]
                        future = executor.submit(worker_process, trt, processos, obj)
                        futures.append(future)

    for future in concurrent.futures.as_completed(futures):
        try:
            result = future.result()
        except Exception as e:
            print(f'Erro: {e}')



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pandora Bot Command Line Interface")
    parser.add_argument("command", choices=["start_certidao", "start_processos", "start_trt", "start_processos_error"], help="Command to execute")

    razao_social = input("Digite o nome da empresa: ")
    cnpj = input("Digite o CNPJ da empresa: ")
    cnpj = cnpj.replace("/", "")
    obj = {'razao_social': razao_social, 'cnpj': cnpj}

    args = parser.parse_args()
    if args.command == "start_certidao":
        start_certidao(obj)
    elif args.command == "start_processos":
        start_processos(obj=obj)
    elif args.command == "start_processos_error":
        start_processos_error(obj)
    elif args.command == "start_trt":
        start_trt(obj)
    


