import sys
import os

# Исправление ошибок Windows (fcntl, curses, termios)
if sys.platform == 'win32':
    class MockModule:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None


    for module_name in ['fcntl', 'termios', 'tty']:
        if module_name not in sys.modules:
            sys.modules[module_name] = MockModule()

import ee
from dotenv import load_dotenv


def initialize_ee(project_id: str = None):
    """Безопасная инициализация Earth Engine для Windows"""
    load_dotenv()

    if project_id is None:
        project_id = os.getenv('GEE_PROJECT_ID')

    if not project_id:
        raise ValueError("❌ Укажите GEE_PROJECT_ID в файле .env")

    try:
        ee.Initialize(project=project_id)
        print(f"✅ Earth Engine инициализирован: {project_id}")
        return ee
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        raise