"""Templates configuration for the web application."""
import pathlib
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=str(pathlib.Path(__file__).parent / "templates"))
