import logging

import requests
from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)

TOKEN_CACHE_KEY = 'tranzak_access_token'
TOKEN_TTL_SECONDS = 5400


class TranzakServiceError(Exception):
    pass


def _build_headers(token=None):
    headers = {
        'X-App-ID': settings.TRANZAK_APP_ID or '',
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'
    return headers


def get_access_token(force_refresh=False):
    if not force_refresh:
        cached_token = cache.get(TOKEN_CACHE_KEY)
        if cached_token:
            return cached_token

    if not settings.TRANZAK_APP_ID or not settings.TRANZAK_APP_KEY:
        raise TranzakServiceError('Tranzak credentials are not configured.')

    url = f'{settings.TRANZAK_BASE_URL}/auth/token'
    payload = {
        'appId': settings.TRANZAK_APP_ID,
        'appKey': settings.TRANZAK_APP_KEY,
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.exception('Unable to fetch Tranzak token.')
        raise TranzakServiceError('Unable to authenticate with Tranzak.') from exc

    if not data.get('success'):
        raise TranzakServiceError(data.get('message') or 'Tranzak token request failed.')

    token = (
        data.get('data', {}).get('token')
        or data.get('token')
        or data.get('accessToken')
    )
    if not token:
        raise TranzakServiceError('Tranzak did not return an access token.')

    cache.set(TOKEN_CACHE_KEY, token, TOKEN_TTL_SECONDS)
    return token


def create_payment_request(payload):
    url = f'{settings.TRANZAK_BASE_URL}/xp021/v1/request/create'
    data = _request_with_token_refresh('post', url, json=payload)

    if not data.get('success'):
        raise TranzakServiceError(data.get('message') or 'Tranzak payment request failed.')

    return data


def fetch_request_details(request_id):
    url = f'{settings.TRANZAK_BASE_URL}/xp021/v1/request/details'
    data = _request_with_token_refresh('get', url, params={'requestId': request_id})

    if not data.get('success'):
        raise TranzakServiceError(data.get('message') or 'Tranzak payment details request failed.')

    return data


def _request_with_token_refresh(method, url, **kwargs):
    for attempt in range(2):
        token = get_access_token(force_refresh=attempt == 1)
        try:
            response = requests.request(
                method,
                url,
                headers=_build_headers(token),
                timeout=20,
                **kwargs,
            )
            if response.status_code == 401 and attempt == 0:
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.exception('Tranzak API request failed for %s %s.', method.upper(), url)
            raise TranzakServiceError('Unable to reach Tranzak right now.') from exc

    raise TranzakServiceError('Unable to authenticate with Tranzak.')
