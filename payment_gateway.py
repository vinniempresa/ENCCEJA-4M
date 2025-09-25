import os
from novaerapayments import NovaEraPaymentsAPI, create_payment_api as create_novaera_api
from for4payments import For4PaymentsAPI, create_payment_api as create_for4_api
from quatrompagamentos import QuatroMPagamentosAPI, create_quatrom_api
from typing import Union

def get_payment_gateway() -> Union[NovaEraPaymentsAPI, For4PaymentsAPI, QuatroMPagamentosAPI]:
    """Factory function to create the appropriate payment gateway instance based on GATEWAY_CHOICE"""
    gateway_choice = os.environ.get("GATEWAY_CHOICE", "FOR4").upper()
    
    if gateway_choice == "NOVAERA":
        return create_novaera_api()
    elif gateway_choice == "FOR4":
        return create_for4_api()
    elif gateway_choice == "4M" or gateway_choice == "QUATROM":
        # Verifica se a chave do 4M está configurada
        if not os.environ.get("QUATROM_PAGAMENTOS_SECRET_KEY"):
            print(f"AVISO: GATEWAY_CHOICE configurado como '{gateway_choice}' mas QUATROM_PAGAMENTOS_SECRET_KEY não encontrada. Usando For4Payments como fallback.")
            return create_for4_api()
        return create_quatrom_api()
    else:
        raise ValueError("GATEWAY_CHOICE must be either 'NOVAERA', 'FOR4', or '4M'/'QUATROM'")
