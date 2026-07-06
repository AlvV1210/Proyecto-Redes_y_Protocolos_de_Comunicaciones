-- PC3 Cooperativa Financiera - Autenticación socios (Banca Web)
SET search_path TO core_bancario, public;

ALTER TABLE socio
    ADD COLUMN IF NOT EXISTS pin_hash VARCHAR(255);

-- PIN demo: últimos 4 dígitos del DNI (ej. DNI 45678901 → PIN 8901)
UPDATE socio SET pin_hash = CASE dni
    WHEN '45678901' THEN '$2b$10$ynXItbXtK2QpGw3mgbfj6u8TjR5xakHh27wU.pLMMro.67m8XjWEe'
    WHEN '12345678' THEN '$2b$10$yDfvoZ7wRVbiAgc9q9Wn/e08uLkJqUwAMYy.sTmJFdT1OM6zfkzIi'
    WHEN '87654321' THEN '$2b$10$7piogyIk.JzM/IMrlecyDumwGxq.aYsLTCRCOj55MNpfBg4KCpFpG'
    WHEN '23456789' THEN '$2b$10$JYWpdntIipuM4zTq8GPbxefCEtgNTubVFdHjCG5sRCharq4f2ws7e'
    WHEN '34567890' THEN '$2b$10$nJy1HKNVPR7yxCDHi9q78uJgogkjILGtefjt7NAiua3eupQjImpYO'
    WHEN '56789012' THEN '$2b$10$6EbSOo6n.SV.ec.fVokqXOIFiLETkf0KYpkE5hqEDA9kFV5a6xUwu'
    WHEN '67890123' THEN '$2b$10$vBHKJ2lryD7TTHqDRIoRnOKCQI65eZMbq7bqV3f.ivLvWjeS0Q0ra'
    WHEN '78901234' THEN '$2b$10$tEaX0LmYNRqGaGSX.NJi1uedFx4L5Or7qBnfef3P.ZokdiBnuNj9i'
END
WHERE pin_hash IS NULL;
