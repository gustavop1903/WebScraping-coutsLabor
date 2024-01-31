from os import getenv

from dotenv import load_dotenv

load_dotenv()

APIKEY_2CAPTCHA = getenv("APIKEY_2CAPTCHA")
SENHA_PJE = getenv("SENHA_PJE")
USUARIO_PJE = getenv("USUARIO_PJE")
#PATH = getenv("PATH")

assert APIKEY_2CAPTCHA, "Environment variable APIKEY_2CAPTCHA not found!"
assert SENHA_PJE, "Environment variable SENHA_PJE not found!"
assert USUARIO_PJE, "Environment variable USUARIO_PJE not found!"
#assert PATH, "Environment variable PATH not found!"