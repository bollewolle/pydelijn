"""Initialize the package."""
from .ShapefileService import ShapefileService
from .STIBService import STIBService
from pystibmvib.client.STIBAPIClient import AbstractSTIBAPIClient, STIBAPIClient

from .domain import *

NAME = "pystibmvib"