import httpx
from conf.conf import settings


async def make_request(
    url: str,
    method: str,
    data: dict = None,
    headers: dict = None
):
    
    if not data:
        data = {}
    timeout = httpx.Timeout(settings.GATEWAY_TIMEOUT)
    async with httpx.AsyncClient(timeout=timeout) as client:
        request = getattr(client, method)
        response = await request(url, json=data, headers=headers)
        new_data = response.json()
        return (new_data, response.status_code)