@echo off
echo =============================================================
echo AVISO: Este script irá EXCLUIR TODOS OS PEDIDOS do sistema!
echo Um backup do banco de dados será feito automaticamente.
echo =============================================================
echo.
set /p CONFIRMAR="Deseja continuar? (S/N): "

if /i "%CONFIRMAR%"=="S" (
    echo.
    echo Iniciando o processo de zerar pedidos...
    cd "C:\Projeto Operacional rev15"
    python manage.py zerar_pedidos --confirmar
    echo.
    echo Processo concluído!
) else (
    echo.
    echo Operação cancelada pelo usuário.
)

pause 