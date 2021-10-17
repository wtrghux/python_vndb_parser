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
SITE = "https://vndb.org"
APP_ICON = os.getcwd() + "\\static\\favicon.ico"
IMGS_PATH = os.getcwd() + "\\media\\"
TABLE_HEADERS = ["Poster", "Title", "Released", "Popularity", "Rating", "Link"]


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
        self.setWindowIcon(QIcon(APP_ICON))

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

    def openVnLink(self):
        for currentQTableWidgetItem in self.ui.tableWidget.selectedItems():
            row = currentQTableWidgetItem.row()
            linkVn = self.ui.tableWidget.item(
                row, len(TABLE_HEADERS) - 1
            ).text()
            QDesktopServices.openUrl(QUrl(linkVn))

    def checkWarnings(self):
        self.ui.tableWidget.setRowCount(0)

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
            imgName = imgLink.split("/")[-1:]
            imgPath = IMGS_PATH + imgName[0]
            if os.path.exists(imgPath):
                return imgPath

            with open(imgPath, "wb") as f:
                f.write(requests.get(imgLink, headers=HEADERS).content)
            return imgPath

        except AttributeError as e:
            print("LOG:", e)
            return os.getcwd() + "\\static\\errorImage.jpg"

    def addListItems(self, titleParameters):

        startTime = time.time()
        if not os.path.exists(IMGS_PATH):
            os.mkdir(IMGS_PATH)
        for row, item in enumerate(titleParameters, start=0):
            titleLink = item[len(item) - 1]
            imgPath = QIcon(self.downloadImg(titleLink))
            self.ui.tableWidget.insertRow(row)
            self.ui.tableWidget.setRowHeight(
                row, (self.iconHeight + self.iconWidth) // 3
            )
            img = QTableWidgetItem()
            img.setIcon(imgPath)
            self.ui.tableWidget.setItem(row, 0, img)
            for j in range(1, len(item) + 1):
                self.ui.tableWidget.setItem(
                    row, j, QTableWidgetItem(item[j - 1])
                )
        endTime = time.time()
        resTime = round(endTime - startTime, 2)
        self.ui.labelTime.setText(f"Время выполнения скрипта: {resTime} сек.")

    def parseSearchResults(self, query):

        html = requests.get(SITE + f"/v?q={query}", headers=HEADERS)
        soup = bs(html.content, "html.parser")
        resultsCount = soup.find("p", class_="center")

        # if title page is returned
        if resultsCount is None:
            return self.parseOnePage(soup)

        # if no results found
        if resultsCount.getText().split()[0] == "0":
            return False

        # if one page with titles list is returned
        pagesNum = soup.find("a", text="last »")
        if pagesNum is None:
            trList = [tr for tr in soup.find_all("tr")][1:]
            return [
                [
                    item.find(class_="tc_title").getText(),
                    item.find(class_="tc_rel").getText(),
                    item.find(class_="tc_pop").getText(),
                    item.find(class_="tc_rating").getText(),
                    SITE + item.find("a").get("href"),
                ]
                for item in trList
            ]

        # if more than one page with results
        pages = pagesNum.get("href").split("&")[1]
        pagesCount = int(pages[2:])
        resultsList = []
        for page in range(1, pagesCount + 1):
            html = requests.get(
                SITE + f"/v?p={page}&q={query}", headers=HEADERS
            )
            soup = bs(html.content, "html.parser")
            trList = [tr for tr in soup.find_all("tr")][1:]
            for item in trList:
                resultsList.append(
                    [
                        item.find(class_="tc_title").getText(),
                        item.find(class_="tc_rel").getText(),
                        item.find(class_="tc_pop").getText(),
                        item.find(class_="tc_rating").getText(),
                        SITE + item.find("a").get("href"),
                    ]
                )
            time.sleep(1)
        return resultsList

    # function to parse exactly title page
    def parseOnePage(self, soup):
        rankings = soup.find(class_="votestats").find_all("p")
        return [
            [
                soup.find(class_="title").getText(),
                soup.find(class_="tc1").getText(),
                rankings[0].getText().split()[-1:][0],
                rankings[1].getText().split()[-1:][0],
                soup.find("base").get("href"),
            ]
        ]

    def closeEvent(self, event):
        if os.path.exists(IMGS_PATH):
            shutil.rmtree(IMGS_PATH)
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle(QStyleFactory.create("Fusion"))
    lab = mywindow()
    lab.show()
    sys.exit(app.exec())
