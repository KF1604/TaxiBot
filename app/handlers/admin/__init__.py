from aiogram import Router
from .admin_panel import router as admin_panel_router
from .admins import router as admins_router
from .drivers import router as drivers_router
from .users import router as users_router
from .stats import router as stats_router
from .ads import router as ads_router
from .register_drivers import router as register_driver
from .sending_payment import sending_router as sending_payment
from .forwarder import router as forwarder

admin_router = Router(name="admin")

admin_router.include_routers(
    admin_panel_router,
    admins_router,
    drivers_router,
    users_router,
    stats_router,
    ads_router,
    register_driver,
    sending_payment,
    forwarder
)