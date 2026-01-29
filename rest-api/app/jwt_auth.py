"""
JWT Service Account Authentication for AEM Classic HTTP API.

Based on: 
- https://experienceleague.adobe.com/en/docs/experience-manager-cloud-service/content/implementing/developing/generating-access-tokens-for-server-side-apis
- https://github.com/adobe/aemcs-api-client-lib
"""

import json
import time
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import jwt
import httpx

logger = logging.getLogger(__name__)


class JWTServiceAccountAuth:
    """
    Handles JWT-based authentication for AEM Classic HTTP API (/api/assets).
    
    This uses the technical account JSON file with certificate and private key
    to generate signed JWT tokens and exchange them for IMS access tokens.
    """
    
    def __init__(self, service_account_json: str):
        """
        Initialize with service account JSON (file path or JSON string).
        
        Args:
            service_account_json: Either:
                - Path to the technical account JSON file (for local dev)
                - JSON string content (for Vercel deployment)
        """
        self.service_account_json = service_account_json
        self.service_account_config: Optional[Dict] = None
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Load service account configuration
        self._load_service_account_config()
    
    def _load_service_account_config(self):
        """Load and parse the service account JSON (from file path or string)."""
        try:
            # Try to parse as JSON string first
            try:
                data = json.loads(self.service_account_json)
                logger.info("Loaded service account config from JSON string")
            except (json.JSONDecodeError, TypeError):
                # Not a JSON string, treat as file path
                with open(self.service_account_json, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded service account config from file: {self.service_account_json}")
            
            # The JSON structure from Adobe Developer Console
            if 'integration' in data:
                integration = data['integration']
                tech_account = integration['technicalAccount']
                
                self.service_account_config = {
                    'ims_endpoint': f"https://{integration.get('imsEndpoint', 'ims-na1.adobelogin.com')}",
                    'ims_org_id': integration.get('org', ''),  # org is at integration level
                    'client_id': tech_account['clientId'],
                    'client_secret': tech_account['clientSecret'],
                    'technical_account_id': integration.get('id', ''),  # id is also at integration level
                    'metascopes': integration.get('metascopes', ''),
                    'private_key': integration['privateKey'],
                    'certificate': integration.get('publicKey', integration.get('cert', '')),
                }
                logger.info(f"Service account loaded for technical account: {self.service_account_config['technical_account_id']}")
            else:
                raise ValueError("Invalid service account JSON format - missing 'integration' key")
                
        except FileNotFoundError:
            logger.error(f"Service account JSON file not found: {self.service_account_json}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in service account: {e}")
            raise
        except KeyError as e:
            logger.error(f"Missing required field in service account JSON: {e}")
            raise
    
    def _create_jwt_token(self) -> str:
        """
        Create a signed JWT token using the private key.
        
        Returns:
            Signed JWT token string
        """
        if not self.service_account_config:
            raise ValueError("Service account config not loaded")
        
        # JWT payload as per Adobe documentation
        # https://experienceleague.adobe.com/en/docs/experience-manager-cloud-service/content/implementing/developing/generating-access-tokens-for-server-side-apis
        current_time = int(time.time())
        expiration_time = current_time + 60 * 60  # 1 hour from now
        
        # Build metascope URL - Adobe requires full URL format
        # e.g., "https://ims-na1.adobelogin.com/s/ent_aem_cloud_api"
        metascopes_raw = self.service_account_config['metascopes']
        if isinstance(metascopes_raw, str):
            metascopes_raw = [metascopes_raw] if metascopes_raw else []
        
        # Format metascopes as full URLs
        metascopes = []
        for scope in metascopes_raw:
            if scope.startswith('http'):
                # Already a full URL
                metascopes.append(scope)
            else:
                # Build the URL: https://{ims_endpoint}/s/{scope}
                ims_host = self.service_account_config['ims_endpoint'].replace('https://', '')
                metascope_url = f"https://{ims_host}/s/{scope}"
                metascopes.append(metascope_url)
        
        logger.debug(f"Metascopes: {metascopes}")
        
        payload = {
            'exp': expiration_time,
            'iss': self.service_account_config['ims_org_id'],  # IMS org ID
            'sub': self.service_account_config['technical_account_id'],  # Technical account ID
            'aud': f"{self.service_account_config['ims_endpoint']}/c/{self.service_account_config['client_id']}",
        }
        
        # Add metascopes as claims (true values)
        for scope in metascopes:
            payload[scope] = True
        
        logger.debug(f"JWT payload (without key): {payload}")
        
        # Sign the JWT with the private key
        private_key = self.service_account_config['private_key']
        
        jwt_token = jwt.encode(
            payload,
            private_key,
            algorithm='RS256'
        )
        
        logger.debug("Created signed JWT token")
        return jwt_token
    
    async def _exchange_jwt_for_access_token(self, jwt_token: str) -> Dict:
        """
        Exchange JWT token for IMS access token.
        
        Args:
            jwt_token: Signed JWT token
            
        Returns:
            Dict with access_token and expires_in
        """
        if not self.service_account_config:
            raise ValueError("Service account config not loaded")
        
        token_endpoint = f"{self.service_account_config['ims_endpoint']}/ims/exchange/jwt/"
        
        data = {
            'client_id': self.service_account_config['client_id'],
            'client_secret': self.service_account_config['client_secret'],
            'jwt_token': jwt_token
        }
        
        logger.debug(f"Exchanging JWT for access token at {token_endpoint}")
        
        try:
            response = await self.client.post(
                token_endpoint,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()
            
            token_data = response.json()
            
            if 'access_token' not in token_data:
                logger.error(f"No access_token in response: {token_data}")
                raise ValueError("Failed to get access token from IMS")
            
            logger.info("Successfully exchanged JWT for access token")
            return token_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during JWT exchange: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error exchanging JWT for access token: {str(e)}")
            raise
    
    async def get_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            Valid IMS access token
        """
        # Check if we have a valid token
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                logger.debug("Using cached JWT service account access token")
                return self.access_token
        
        # Generate new token
        logger.info("Generating new JWT service account access token")
        
        # Step 1: Create signed JWT
        jwt_token = self._create_jwt_token()
        
        # Step 2: Exchange JWT for access token
        token_data = await self._exchange_jwt_for_access_token(jwt_token)
        
        # Step 3: Store token and expiration
        self.access_token = token_data['access_token']
        expires_in = token_data.get('expires_in', 86400)  # Default 24 hours
        
        # Refresh 5 minutes before expiration
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
        
        logger.info(f"JWT service account token obtained, expires in {expires_in} seconds")
        return self.access_token
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
