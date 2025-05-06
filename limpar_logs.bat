@echo off
echo Iniciando limpeza de logs de produtos antigos...
cd "C:\Projeto Operacional rev15"
python manage.py limpar_logs_produtos
echo Limpeza concluída!
pause 