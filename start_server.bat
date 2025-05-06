@echo off
echo Iniciando servidor em 0.0.0.0:8000
echo Este servidor estara disponivel na rede local em: http://192.168.15.69:8000

:: Ativa o ambiente virtual (se necessário)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist env\Scripts\activate.bat (
    call env\Scripts\activate.bat
)

:: Inicia o servidor em 0.0.0.0:8000 para aceitar conexões de qualquer endereço IP
python manage.py runserver 0.0.0.0:8000

pause 