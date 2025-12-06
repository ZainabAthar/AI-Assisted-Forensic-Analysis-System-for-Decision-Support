# CAT-Net-Webapp/app/catnet_core/lib/__init__.py

# Expose the core submodules required by the rest of the application
from . import config
from . import core
from . import models
from . import utils 

# Optional: if the old script defined 'models' and 'config' globally within lib
# You could also add specific imports, but this should suffice:
# from .config.config import config as main_config
# from .config.config import update_config as main_update_config
# from .utils.utils import FullModel