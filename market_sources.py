"""JSON connectors. Permission checks precede every network request."""
import ipaddress
import json
import socket
from datetime import datetime, timezone
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from market_engine import stamp

class SourceBlocked(ValueError):
    pass

def authorize(source, now=None):
    now = now or datetime.now(timezone.utc)
    if source.get('enabled') is not True or source.get('verified') is not True:
        raise SourceBlocked('disabled or unverified source')
    for field in ('id', 'endpoint', 'permission_url', 'provenance_url', 'verified_at'):
        if not isinstance(source.get(field), str) or not source[field].strip():
            raise SourceBlocked('missing evidence: '+field)
    if not source['id'].replace('-', '').replace('_', '').isalnum():
        raise SourceBlocked('invalid source id')
    if source.get('free') is not True or source.get('automation_allowed') is not True or source.get('storage_allowed') is not True:
        raise SourceBlocked('free automated collection/storage not authorized')
    if source.get('interval_minutes', 0) < 30:
        raise SourceBlocked('source frequency must be at least 30 minutes')
    if source.get('connector') not in ('json_api', 'public_json'):
        raise SourceBlocked('unsupported connector')
    if not 0 <= (now-stamp(source['verified_at'])).total_seconds() <= 90*86400:
        raise SourceBlocked('verification expired or future')
    for field in ('endpoint', 'permission_url', 'provenance_url'):
        url=urlsplit(source[field])
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.fragment:
            raise SourceBlocked('evidence and endpoint require HTTPS, no embedded credentials')

def public_host(endpoint):
    url=urlsplit(endpoint)
    if url.port not in (None,443):
        raise SourceBlocked('HTTPS port required')
    for result in socket.getaddrinfo(url.hostname,443,type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(result[4][0]).is_global:
            raise SourceBlocked('private/non-public destination')

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SourceBlocked('redirect refused; review endpoint')

def fetch_json(source):
    authorize(source)
    public_host(source['endpoint'])
    request=Request(source['endpoint'],headers={'Accept':'application/json','User-Agent':'FUTTrader27-Test/2.0'})
    # No retries, cookies, proxy rotation, browser impersonation or challenge handling.
    with build_opener(NoRedirect).open(request,timeout=20) as response:
        if response.status!=200 or response.headers.get_content_type()!='application/json':
            raise ValueError('expected HTTP 200 application/json')
        raw=response.read(8_000_001)
        if len(raw)>8_000_000:
            raise ValueError('response exceeds 8 MB')
    return json.loads(raw)

class JsonAPI:
    """Canonical FC27 contract; never guesses platform, tradeability or timestamps."""
    def normalize(self,payload,source):
        if not isinstance(payload,dict):
            raise ValueError('JSON object required')
        if payload.get('source_id')!=source['id']:
            raise ValueError('source identity mismatch')
        return payload

class PublicJSON(JsonAPI):
    """Public feed using the same explicit contract, plus reusable-data license."""
    def normalize(self,payload,source):
        if not source.get('data_license') or not source.get('license_url'):
            raise SourceBlocked('public feed requires data license evidence')
        return super().normalize(payload,source)

CONNECTORS={'json_api':JsonAPI(),'public_json':PublicJSON()}

def collect(source,transport=fetch_json):
    authorize(source)
    connector=CONNECTORS[source['connector']]
    if isinstance(connector,PublicJSON) and (not source.get('data_license') or not source.get('license_url')):
        raise SourceBlocked('public feed requires data license evidence')
    return connector.normalize(transport(source),source)
