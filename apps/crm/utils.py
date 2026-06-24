def calcular_sistema_solar(consumo_kwh, irradiacao, potencia_painel_wp=550):
    """
    Retorna um dicionário com o dimensionamento completo.
    """
    # 1. Potência do Sistema (kWp) = Consumo / (30 dias * Irradiação * Eficiência)
    eficiencia = 0.80
    potencia_sistema_kwp = consumo_kwh / (30 * irradiacao * eficiencia)
    
    # 2. Quantidade de Placas = (Potência do Sistema em Watts) / Potência de 1 Painel
    potencia_sistema_w = potencia_sistema_kwp * 1000
    qtd_placas = math.ceil(potencia_sistema_w / potencia_panel_wp) # Arredonda para cima
    
    # Reajusta a potência final com base no número real de placas arredondado
    potencia_final_kwp = (qtd_placas * potencia_painel_wp) / 1000
    
    # 3. Área Necessária (Cada painel de 550Wp tem ~2.2 m²)
    area_necessaria = qtd_placas * 2.2
    
    # 4. Peso Estimado (Painel + Estrutura de fixação ~30kg por módulo)
    peso_total = qtd_placas * 30
    
    return {
        'potencia_sistema_kwp': round(potencia_final_kwp, 2),
        'qtd_placas': qtd_placas,
        'area_necessaria_m2': round(area_necessaria, 2),
        'peso_total_kg': round(peso_total, 2)
    }