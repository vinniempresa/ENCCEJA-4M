import os
import requests
from datetime import datetime
from flask import current_app
from typing import Dict, Any, Optional
import random
import string


class QuatroMPagamentosAPI:
    API_URL = "https://app.4mpagamentos.com/api/v1"

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests using Bearer token authentication"""
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.secret_key}'
        }

    def _generate_random_email(self, name: str) -> str:
        clean_name = ''.join(e.lower() for e in name if e.isalnum())
        random_num = ''.join(random.choices(string.digits, k=4))
        domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        domain = random.choice(domains)
        return f"{clean_name}{random_num}@{domain}"

    def _generate_random_phone(self) -> str:
        ddd = str(random.randint(11, 99))
        number = ''.join(random.choices(string.digits, k=8))
        return f"{ddd}{number}"

    def create_pix_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a PIX payment request using 4M Pagamentos API"""
        # Validação da chave secreta
        if not self.secret_key:
            current_app.logger.error("Token de autenticação 4M Pagamentos não fornecido")
            raise ValueError("Token de autenticação não foi configurado")
        elif len(self.secret_key) < 10:
            current_app.logger.error(
                f"Token de autenticação 4M Pagamentos muito curto ({len(self.secret_key)} caracteres)"
            )
            raise ValueError("Token de autenticação inválido (muito curto)")
        else:
            current_app.logger.info(
                f"Utilizando token 4M Pagamentos: {self.secret_key[:3]}...{self.secret_key[-3:]} ({len(self.secret_key)} caracteres)"
            )

        # Log dos dados recebidos para processamento
        safe_data = {k: v for k, v in data.items()}
        if 'cpf' in safe_data and safe_data['cpf']:
            safe_data['cpf'] = f"{safe_data['cpf'][:3]}...{safe_data['cpf'][-2:]}" if len(safe_data['cpf']) > 5 else "***"
        current_app.logger.info(f"Dados recebidos para pagamento 4M: {safe_data}")

        # Suportar tanto format customer_* quanto format padrão (name, cpf, email, phone)
        # para manter compatibilidade com outras APIs
        customer_name = data.get('customer_name') or data.get('name')
        customer_cpf = data.get('customer_cpf') or data.get('cpf')
        customer_email = data.get('customer_email') or data.get('email')
        customer_phone = data.get('customer_phone') or data.get('phone')
        
        # Validação dos campos obrigatórios
        if not customer_name or not data.get('amount'):
            missing_fields = []
            if not customer_name:
                missing_fields.append('name/customer_name')
            if not data.get('amount'):
                missing_fields.append('amount')
            current_app.logger.error(f"Campos obrigatórios ausentes: {missing_fields}")
            raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing_fields)}")

        try:
            # Validação e conversão do valor
            try:
                amount = float(data['amount'])
                current_app.logger.info(f"Valor do pagamento 4M: R$ {amount:.2f}")
            except (ValueError, TypeError) as e:
                current_app.logger.error(f"Erro ao converter valor do pagamento: {str(e)}")
                raise ValueError(f"Valor de pagamento inválido: {data['amount']}")

            if amount <= 0:
                current_app.logger.error(f"Valor do pagamento não positivo: {amount}")
                raise ValueError("Valor do pagamento deve ser maior que zero")

            # Processamento do CPF
            cpf = ''
            if customer_cpf:
                cpf = ''.join(filter(str.isdigit, str(customer_cpf)))
                if len(cpf) != 11:
                    current_app.logger.warning(f"CPF com formato inválido: {cpf} (comprimento: {len(cpf)})")
                else:
                    current_app.logger.info(f"CPF validado: {cpf[:3]}...{cpf[-2:]}")

            # Validação e geração de email se necessário
            email = customer_email
            if not email or '@' not in email:
                email = self._generate_random_email(customer_name)
                current_app.logger.info(f"Email gerado automaticamente: {email}")
            else:
                current_app.logger.info(f"Email fornecido: {email}")

            # Processamento do telefone
            phone = customer_phone or ''
            if not phone or not isinstance(phone, str) or len(phone.strip()) < 10:
                phone = self._generate_random_phone()
                current_app.logger.info(f"Telefone gerado automaticamente: {phone}")
            else:
                # Remove any non-digit characters from the phone
                phone = ''.join(filter(str.isdigit, phone))
                current_app.logger.info(f"Telefone processado: {phone}")

            # Preparação dos dados para a API 4M Pagamentos
            payment_data = {
                "amount": str(amount),  # 4M API espera string
                "customer_name": customer_name,
                "customer_email": email,
                "customer_cpf": cpf if cpf else None,
                "customer_phone": phone,
                "description": data.get('description', 'Pagamento via PIX'),
                "product_id": data.get('product_id')  # Opcional para configurações específicas do produto
            }

            # Remove campos nulos para evitar problemas na API
            payment_data = {k: v for k, v in payment_data.items() if v is not None}

            current_app.logger.info(f"Dados de pagamento formatados para 4M: {payment_data}")
            current_app.logger.info(f"Endpoint API: {self.API_URL}/payments")
            current_app.logger.info("Enviando requisição para API 4M Pagamentos...")

            try:
                response = requests.post(
                    f"{self.API_URL}/payments",
                    json=payment_data,
                    headers=self._get_headers(),
                    timeout=30
                )

                current_app.logger.info(f"Resposta 4M recebida (Status: {response.status_code})")
                current_app.logger.debug(f"Resposta completa: {response.text}")

                if response.status_code in [200, 201]:
                    response_data = response.json()
                    current_app.logger.info(f"Resposta da API 4M: {response_data}")

                    # A API 4M retorna dados dentro do objeto 'data'
                    data_obj = response_data.get('data', response_data)
                    
                    return {
                        'id': data_obj.get('transaction_id') or data_obj.get('id'),
                        'pixCode': data_obj.get('pix_code') or data_obj.get('pixCode'),
                        'pixQrCode': data_obj.get('pix_qr_code') or data_obj.get('pixQrCode'),
                        'expiresAt': data_obj.get('expires_at') or data_obj.get('expiresAt'),
                        'status': data_obj.get('status', 'pending')
                    }
                elif response.status_code == 401:
                    current_app.logger.error("Erro de autenticação com a API 4M Pagamentos")
                    raise ValueError("Falha na autenticação com a API 4M Pagamentos. Verifique a chave de API.")
                else:
                    error_message = 'Erro ao processar pagamento'
                    try:
                        error_data = response.json()
                        if isinstance(error_data, dict):
                            error_message = error_data.get('message') or error_data.get('error') or '; '.join(error_data.get('errors', []))
                            current_app.logger.error(f"Erro da API 4M Pagamentos: {error_message}")
                    except Exception as e:
                        error_message = f'Erro ao processar pagamento (Status: {response.status_code})'
                        current_app.logger.error(f"Erro ao processar resposta da API: {str(e)}")
                    raise ValueError(error_message)

            except requests.exceptions.RequestException as e:
                current_app.logger.error(f"Erro de conexão com a API 4M Pagamentos: {str(e)}")
                raise ValueError("Erro de conexão com o serviço de pagamento. Tente novamente em alguns instantes.")

        except ValueError as e:
            current_app.logger.error(f"Erro de validação: {str(e)}")
            raise
        except Exception as e:
            current_app.logger.error(f"Erro inesperado ao processar pagamento: {str(e)}")
            raise ValueError("Erro interno ao processar pagamento. Por favor, tente novamente.")

    def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Check the status of a payment using 4M Pagamentos API"""
        try:
            current_app.logger.info(f"[4M] Verificando status do pagamento {payment_id}")
            response = requests.get(
                f"{self.API_URL}/payments/{payment_id}",
                headers=self._get_headers(),
                timeout=30
            )

            current_app.logger.info(f"Status check response 4M (Status: {response.status_code})")
            current_app.logger.debug(f"Status check response body: {response.text}")

            if response.status_code == 200:
                payment_data = response.json()
                current_app.logger.info(f"Payment data received from 4M: {payment_data}")

                # Map 4M Pagamentos status to our application status
                status_mapping = {
                    'PENDING': 'pending',
                    'PROCESSING': 'pending',
                    'PAID': 'completed',
                    'APPROVED': 'completed',
                    'COMPLETED': 'completed',
                    'EXPIRED': 'failed',
                    'FAILED': 'failed',
                    'CANCELED': 'cancelled',
                    'CANCELLED': 'cancelled'
                }

                current_status = payment_data.get('status', 'PENDING').upper()
                mapped_status = status_mapping.get(current_status, 'pending')

                current_app.logger.info(f"Payment {payment_id} status: {current_status} -> {mapped_status}")

                # Se o pagamento foi confirmado, registrar evento para o Facebook Pixel
                if mapped_status == 'completed':
                    current_app.logger.info(
                        f"[FACEBOOK_PIXEL] Evento de conversão para pagamento {payment_id} - 4M Pagamentos"
                    )

                # A API 4M pode retornar dados dentro do objeto 'data'
                data_obj = payment_data.get('data', payment_data)
                
                return {
                    'status': mapped_status,
                    'original_status': current_status,
                    'pix_qr_code': data_obj.get('pix_qr_code') or data_obj.get('pixQrCode'),
                    'pix_code': data_obj.get('pix_code') or data_obj.get('pixCode'),
                    'transaction_id': data_obj.get('transaction_id') or data_obj.get('id')
                }
            elif response.status_code == 404:
                current_app.logger.warning(f"Payment {payment_id} not found in 4M")
                return {'status': 'pending', 'original_status': 'PENDING'}
            else:
                error_message = f"Failed to fetch payment status from 4M (Status: {response.status_code})"
                current_app.logger.error(error_message)
                return {'status': 'pending', 'original_status': 'PENDING'}

        except Exception as e:
            current_app.logger.error(f"Error checking payment status in 4M: {str(e)}")
            return {'status': 'pending', 'original_status': 'PENDING'}

    def create_encceja_payment(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar um pagamento PIX para a taxa do Encceja usando 4M Pagamentos"""
        current_app.logger.info(f"Solicitação de pagamento Encceja via 4M recebida: {user_data}")

        # Validação dos dados obrigatórios
        if not user_data:
            current_app.logger.error("Dados de usuário vazios")
            raise ValueError("Nenhum dado de usuário fornecido")

        if not user_data.get('nome'):
            current_app.logger.error("Nome do usuário não fornecido")
            raise ValueError("Nome do usuário é obrigatório")

        if not user_data.get('cpf'):
            current_app.logger.error("CPF do usuário não fornecido")
            raise ValueError("CPF do usuário é obrigatório")

        # Determinar o valor baseado no desconto
        has_discount = user_data.get('has_discount', False)
        amount = 49.70 if has_discount else 93.40
        current_app.logger.info(f"Valor da taxa Encceja via 4M: R$ {amount:.2f} (desconto: {has_discount})")

        try:
            # Formatar os dados para o pagamento
            payment_data = {
                'customer_name': user_data.get('nome'),
                'customer_email': user_data.get('email'),
                'customer_cpf': user_data.get('cpf'),
                'amount': amount,
                'customer_phone': user_data.get('telefone'),
                'description': 'Taxa de Inscrição ENCCEJA 2025'
            }

            current_app.logger.info("Chamando API de pagamento PIX via 4M Pagamentos")
            result = self.create_pix_payment(payment_data)
            current_app.logger.info(f"Pagamento Encceja criado com sucesso via 4M, ID: {result.get('id')}")
            return result

        except Exception as e:
            current_app.logger.error(f"Erro ao processar pagamento Encceja via 4M: {str(e)}")
            raise ValueError(f"Erro ao processar pagamento: {str(e)}")


def create_quatrom_api(secret_key: Optional[str] = None) -> QuatroMPagamentosAPI:
    """Factory function to create QuatroMPagamentosAPI instance"""
    if secret_key is None:
        secret_key = os.environ.get("QUATROM_PAGAMENTOS_SECRET_KEY")
        if not secret_key:
            raise ValueError("QUATROM_PAGAMENTOS_SECRET_KEY não configurada no ambiente")
    return QuatroMPagamentosAPI(secret_key)