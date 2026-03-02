from decouple import config

DJANGO_ENV = config("DJANGO_ENV", default="dev")

if DJANGO_ENV == "prod":
    from .prod import *
else:
    from .dev import *
