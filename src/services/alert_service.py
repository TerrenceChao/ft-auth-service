from ..configs.exceptions import ServerException
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


# TODO: implement it in infra
class IAlertService:

    async def exceed_retry_alert(self, alert_msg: str, max_retry: int):
        # slack, TG, email, SMS, ... alert
        log.error(f'{alert_msg} retry:{max_retry}')
        raise ServerException(msg=f'{alert_msg} retry:{max_retry}')

    async def exception_alert(self, err_msg: str, e: any):
        # slack, TG, email, SMS, ... alert
        log.error(f'{err_msg} {e.__str__()}')
        raise ServerException(msg=f'{err_msg}')
