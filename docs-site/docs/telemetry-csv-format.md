# Formato CSV de Telemetria

## Colunas Canônicas Esperadas

O CSV de telemetria deve conter as seguintes colunas:

- `lap_dist_pct`: Percentual da volta (0 a 100)
- `speed`: Velocidade
- `throttle`: Uso de acelerador (0 a 1)
- `brake`: Uso de freio (0 a 1)
- `steering`: Ângulo do volante
- `gear`: Marcha

## Descrição das Colunas

- **lap_dist_pct**: Representa o progresso da volta de 0% (linha de chegada) a 100% (volta completa)
- **speed**: Velocidade do veículo em km/h
- **throttle**: Porcentagem de acelerador (`0 = nenhum`, `1 = 100%`)
- **brake**: Porcentagem de freio (`0 = nenhum`, `1 = 100%`)
- **steering**: Ângulo do volante em graus
- **gear**: Marcha atual (1, 2, 3, etc.)

## Exemplo Mínimo

```csv
lap_dist_pct,speed,throttle,brake
0,180,0.8,0
50,190,1.0,0
100,200,0.7,0.2
```

## Notas

- No MVP atual, o CSV precisa estar em formato compatível com as colunas canônicas
- A normalização por distância (`lap_dist_pct`) é essencial para comparação correta
- Valores numéricos devem estar em formato padrão (ponto decimal, não vírgula)
