from .bot_config import BotConfig
from .__dash_ring_handler import _DashRingHandler

class Logger:
    def __init__(self, cfg: BotConfig):
        self.cfg = cfg
        self.log = logging.getLogger("RazTraderPlus")
        self.ring = _DashRingHandler(maxlen=_env_int("DASH_LOG_RING", 400))
        level = logging.INFO
        self.log.setLevel(level)
        logging.getLogger().setLevel(level)
        _ensure_dir(os.path.join("logs", "trading_bot.log"))
        log_path = os.path.join("logs", "trading_bot.log")
        fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        try:
            max_mb = int(_env_int("LOG_ROTATE_MB", 2) or 2)
        except Exception:
            max_mb = 2
        max_mb = max(1, min(20, int(max_mb)))
        try:
            backups = int(_env_int("LOG_ROTATE_BACKUPS", 3) or 3)
        except Exception:
            backups = 3
        backups = max(1, min(10, int(backups)))
        fh = RotatingFileHandler(log_path, maxBytes=max_mb * 1024 * 1024, backupCount=backups, encoding="utf-8")
        fh.setFormatter(fmt)
        fh.setLevel(level)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        ch.setLevel(level)
        root = logging.getLogger()
        if not getattr(Logger, "_configured", False):
            root.addHandler(fh)
            root.addHandler(self.ring)
            if not cfg.dash_enabled:
                root.addHandler(ch)
            Logger._configured = True
        try:
            self.log.info("Logging initialized | dash=%s", cfg.dash_enabled)
        except NotImplementedError:
            try:
                print("[SAFE-LOGGING] Logging initialized | dash=%s" % (cfg.dash_enabled,))
            except Exception:
                pass
        except Exception:
            try:
                print("[SAFE-LOGGING] Logging init skipped")
            except Exception:
                pass