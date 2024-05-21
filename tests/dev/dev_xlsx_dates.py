from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

wb = Workbook(iso_dates=True)
ws = wb.active

ws.append(["Now", datetime.now()])

dev_tmp_folder = Path(__file__).parent.joinpath("tmp")
dev_tmp_folder.mkdir(exist_ok=True, parents=True)

wb.save(filename=dev_tmp_folder.joinpath("test_xlsx_iso-dates.xlsx"))
