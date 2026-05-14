from loguru import logger
import sys
from app.core.config import settings

# إعدادات الـ logging
logger.remove()  # إزالة الـ handler الافتراضي

# إضافة handler للـ console
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level="INFO" if not settings.DEBUG else "DEBUG"
)

# إضافة handler لملف logs
logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}",
    level="INFO"
)

# تسجيل أحداث authentication
def log_auth_event(email: str, success: bool, error: str = None):
    if success:
        logger.info(f"Authentication SUCCESS: {email}")
    else:
        logger.warning(f"Authentication FAILED: {email} - {error}")

# تسجيل الأخطاء
def log_error(error: Exception, context: str = ""):
    logger.error(f"Error in {context}: {str(error)}", exc_info=True)