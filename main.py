from PyQt5.QtWidgets import (
    QTableWidgetItem,
    QStyleFactory,
    QApplication,
    QMainWindow,
    QMessageBox,
    QHeaderView,
)
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtCore import QSize, QUrl
from bs4 import BeautifulSoup as bs
from window import Ui_MainWindow
import requests
import shutil
import time
import sys
import os


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 YaBrowser/19.10.2.195 Yowser/2.5 Safari/537.36"
}
TABLE_HEADERS = ["Poster", "Title", "Released", "Popularity", "Rating", "Link"]
SITE = "https://vndb.org"
IMGS_PATH = os.getcwd() + "\media\\"


class mywindow(QMainWindow):
    def __init__(self):
        super(mywindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.iconWidth = 80
        self.iconHeight = 240
        self.title = "VNDB parser (for fun)"
        self.initUI()

    def initUI(self):
        self.setWindowTitle(
            f"{self.title} – {QApplication.applicationName()} {QApplication.applicationVersion()}"
        )

        self.ui.tableWidget.setIconSize(QSize(self.iconWidth, self.iconHeight))
        self.ui.tableWidget.setHorizontalHeaderLabels(TABLE_HEADERS)
        for key, value in zip([0, 1, 2, 3, 4], [88, 500, 100, 80, 80]):
            self.ui.tableWidget.setColumnWidth(key, value)
        for i in range(6):
            self.ui.tableWidget.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.Fixed
            )
        self.ui.tableWidget.doubleClicked.connect(self.openVnLink)

        self.ui.searchInp.returnPressed.connect(self.ui.searchBtn.click)
        self.ui.searchBtn.clicked.connect(self.checkWarnings)
        self.ui.exitButton.clicked.connect(self.exit)

    def openVnLink(self):
        for currentQTableWidgetItem in self.ui.tableWidget.selectedItems():
            row = currentQTableWidgetItem.row()
            linkVn = self.ui.tableWidget.item(
                row, len(TABLE_HEADERS) - 1
            ).text()
            QDesktopServices.openUrl(QUrl(linkVn))

    def checkWarnings(self):
        query = self.ui.searchInp.text()
        if query == "":
            QMessageBox.warning(self, "Error", "Заполните ввод!")
            return 0

        resultsList = self.parseSearchResults(query)
        if resultsList == False:
            QMessageBox.information(self, "No result", "Ничего не найдено")
            return 0

        self.addListItems(resultsList)
        return 1

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
            return os.getcwd() + "\\errorImage.jpg"

    def addListItems(self, resultsList):

        if not os.path.exists(IMGS_PATH):
            os.mkdir(IMGS_PATH)
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

    def parseSearchResults(self, query):

        html = requests.get(SITE + f"/v?q={query}", headers=HEADERS)
        soup = bs(html.content, "html.parser")
        if soup.find("table") is None:
            return self.parseOnePage()

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
            time.sleep(1)
        return resultsList

    def parseOnePage(self):

        return 0

    def exit(self):
        if os.path.exists(IMGS_PATH):
            shutil.rmtree(IMGS_PATH)
        self.close()


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle(QStyleFactory.create("Fusion"))
    lab = mywindow()
    lab.show()
    sys.exit(app.exec())
