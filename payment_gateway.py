import os
from novaerapayments import NovaEraPaymentsAPI, create_payment_api as create_novaera_api
from for4payments import For4PaymentsAPI, create_payment_api as create_for4_api
from quatrompagamentos import QuatroMPagamentosAPI, create_quatrom_api
from typing import Union

def get_payment_gateway() -> Union[NovaEraPaymentsAPI, For4PaymentsAPI, QuatroMPagamentosAPI]:
    """Factory function to create the appropriate payment gateway instance based on GATEWAY_CHOICE"""
    
    # Prioridade: Se 4M key existe, usar 4M independente de GATEWAY_CHOICE
    quatrom_key = os.environ.get("QUATROM_PAGAMENTOS_SECRET_KEY")
    gateway_choice = os.environ.get("GATEWAY_CHOICE", "").upper()
    
    if quatrom_key:
        print("INFO: 4M Pagamentos key encontrada. Forçando uso do 4M Pagamentos para PIX autênticos.")
        return create_quatrom_api()
    
    # Se não tem 4M key, usar outras opções
    if gateway_choice == "NOVAERA":
        return create_novaera_api()
    elif gateway_choice == "4M" or gateway_choice == "QUATROM":
        print("ERROR: GATEWAY_CHOICE configurado como 4M mas QUATROM_PAGAMENTOS_SECRET_KEY não encontrada. Usando For4Payments.")
        return create_for4_api()
    else:
        # Padrão For4
        return create_for4_api()
