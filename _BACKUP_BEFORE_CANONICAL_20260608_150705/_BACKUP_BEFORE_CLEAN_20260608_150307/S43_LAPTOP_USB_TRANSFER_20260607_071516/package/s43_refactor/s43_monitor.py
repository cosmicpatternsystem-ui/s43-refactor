import sys
import os
import logging
import importlib.util

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MONITOR - %(message)s'
)
logger = logging.getLogger(__name__)

def patch_and_monitor():
    module_name = "s43"
    file_path = "s43.py"
    
    if not os.path.exists(file_path):
        logger.error(f"File {file_path} not found.")
        return

    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        s43_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(s43_module)
        
        target_class_name = "TradingBotOps"
        if hasattr(s43_module, target_class_name):
            target_class = getattr(s43_module, target_class_name)
            
            for attr_name in dir(target_class):
                attr_value = getattr(target_class, attr_name)
                if callable(attr_value) and not attr_name.startswith("__"):
                    def make_wrapper(func, name):
                        def wrapper(*args, **kwargs):
                            logger.info(f"CALL: {target_class_name}.{name}")
                            return func(*args, **kwargs)
                        return wrapper
                    
                    setattr(target_class, attr_name, make_wrapper(attr_value, attr_name))
            
            logger.info(f"Successfully patched {target_class_name}")
            
            if hasattr(s43_module, "main"):
                logger.info("Starting main process...")
                s43_module.main()
        else:
            logger.error(f"Class {target_class_name} not found in {file_path}")
            
    except Exception as e:
        logger.error(f"Monitor failure: {str(e)}")

if __name__ == "__main__":
    patch_and_monitor()
