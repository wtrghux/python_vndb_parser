from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QStyleFactory,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)
from PyQt5.QtGui import (
    QFont,
    QIcon,
    QPalette,
    QColor,
    QImage,
    QBrush,
    QDesktopServices,
)
from PyQt5.QtCore import Qt, QSize
from bs4 import BeautifulSoup as bs
from window import Ui_MainWindow
import requests
import shutil
import sys
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 YaBrowser/19.10.2.195 Yowser/2.5 Safari/537.36"
}
TABLE_HEADERS = ["Poster", "Title", "Released", "Popularity", "Rating", "Link"]
SITE = "https://vndb.org"
IMGS_PATH = os.getcwd() + "\media\\"
if not os.path.exists(IMGS_PATH):
    os.mkdir(IMGS_PATH)


class mywindow(QMainWindow):
    def __init__(self):
        super(mywindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # self.size_horizontal = 420
        # self.size_vertical = 200
        self.iconWidth = 70
        self.iconHeight = 210
        self.title = "VNDB (test)"
        self.initUI()

    def initUI(self):
        # self.setFixedSize(self.size_horizontal, self.size_vertical)
        self.ui.tableWidget.setIconSize(QSize(self.iconWidth, self.iconHeight))
        self.setWindowTitle(
            f"{self.title} – {QApplication.applicationName()} {QApplication.applicationVersion()}"
        )
        self.ui.tableWidget.setHorizontalHeaderLabels(TABLE_HEADERS)

        self.ui.searchButton.clicked.connect(self.checkWarnings)
        self.ui.exitButton.clicked.connect(self.exit)

    def checkWarnings(self):
        query = self.ui.searchInput.text()
        if query == "":
            QMessageBox.warning(self, "Error", "Заполните ввод!")
            return 0
        resultsList = self.parseSearchResults(query)
        if resultsList == False:
            QMessageBox.information(self, "No result", "Ничего не найдено")
            return 0
        self.addListItems(resultsList)

    def downloadImg(self, link):
        html = requests.get(link, headers=HEADERS)
        soup = bs(html.content, "html.parser")
        try:
            imgTag = soup.find(class_="vnimg").find("img")
            imgLink = imgTag.get("src")
            imgName = imgLink.split("/")[5]
            imgPath = IMGS_PATH + imgName
            if os.path.exists(imgPath):
                return imgPath
            with open(imgPath, "wb") as f:
                f.write(requests.get(imgLink, headers=HEADERS).content)
            return imgPath
        except AttributeError as e:
            print("LOG:", e)
            return os.getcwd() + "errorImage.jpg"

    def addListItems(self, resultsList):
        for row, item in enumerate(resultsList, start=0):
            titleLink = SITE + item.find("a").get("href")
            imgPath = QIcon(self.downloadImg(titleLink))
            titleParameters = [
                item.find(class_="tc_title").getText(),
                item.find(class_="tc_rel").getText(),
                item.find(class_="tc_pop").getText(),
                item.find(class_="tc_rating").getText(),
                titleLink,
            ]
            self.ui.tableWidget.insertRow(row)
            self.ui.tableWidget.setRowHeight(
                row, (self.iconHeight + self.iconWidth) // 3
            )
            img = QTableWidgetItem()
            img.setIcon(imgPath)
            self.ui.tableWidget.setItem(row, 0, img)
            for j in range(1, len(titleParameters) + 1):
                self.ui.tableWidget.setItem(
                    row, j, QTableWidgetItem(titleParameters[j - 1])
                )
        self.ui.tableWidget.resizeColumnsToContents()

    def parseSearchResults(self, query):
        html = requests.get(SITE + f"/v?q={query}", headers=HEADERS)
        soup = bs(html.content, "html.parser")
        if soup.find("table") is None:
            return False
        pagesNum = soup.find("a", text="last »")
        if pagesNum is None:
            return [tr for tr in soup.find_all("tr")][1:]
        pages = pagesNum.get("href").split("&")[1]
        pagesCount = int(pages[2:])
        resultsList = []
        for page in range(1, pagesCount + 1):
            html = requests.get(
                SITE + f"/v?p={page}&q={query}", headers=HEADERS
            )
            soup = bs(html.content, "html.parser")
            for item in soup.find_all("tr")[1:]:
                resultsList.append(item)
        return resultsList

    def parseOnePage(self):
        return 0

    def exit(self):
        shutil.rmtree(IMGS_PATH)
        self.close()


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle(QStyleFactory.create("Fusion"))
    lab = mywindow()
    lab.show()
    sys.exit(app.exec())
