-- Script SQL para tornar a coluna pessoa_id NULL em titulos_financeiros
-- Execute este script no MySQL Workbench ou outro cliente MySQL

USE serrana_db;

-- Remover a constraint foreign key temporariamente
ALTER TABLE titulos_financeiros 
DROP FOREIGN KEY titulos_financeiros_ibfk_1;

-- Alterar a coluna para aceitar NULL
ALTER TABLE titulos_financeiros 
MODIFY COLUMN pessoa_id BIGINT NULL;

-- Recriar a constraint foreign key
ALTER TABLE titulos_financeiros 
ADD CONSTRAINT titulos_financeiros_ibfk_1 
FOREIGN KEY (pessoa_id) REFERENCES pessoas(id) 
ON DELETE RESTRICT;

-- Verificar alteração
DESCRIBE titulos_financeiros;
