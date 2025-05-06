-- Resetar a sequência para um valor superior ao maior ID existente
SELECT setval('escolas_supervisor_id_seq', (SELECT MAX(id) FROM escolas_supervisor), true);

-- Verificar o valor atual da sequência
SELECT currval('escolas_supervisor_id_seq'); 