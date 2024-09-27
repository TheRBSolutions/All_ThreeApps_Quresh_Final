from openpyxl import load_workbook
from openpyxl_image_loader import SheetImageLoader
from PIL import Image
import io

path = r"C:\Users\Usama Ahmed\Documents\Quresh_Database_Partial\Quresh_Database\static\6206 rev Al Rumooz Trading LLC.xlsx"
workbook = load_workbook(path)

sheet = workbook.active
image_loader = SheetImageLoader(sheet)

image = image_loader.get("B8") # Cell in which image's top left corner 

# image.save(fr"C:\Users\Usama Ahmed\Documents\Quresh_Database_Partial\Quresh_Database\static\dummy.{image.format}")
image.show()
