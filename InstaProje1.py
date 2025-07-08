print("Bu kod ile birlikte Takipçi ve Takip Ettiğiniz kullanıcıları görebilecek, ve Excel'e bastırabileceksiniz.")

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import re
import pandas as pd
from openpyxl import load_workbook
from kullanici import username, password


class Instagram:
    def __init__(self, username, password):
        self.browser = webdriver.Edge()
        self.username = username
        self.password = password

    def signIn(self):
        self.browser.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)
        self.browser.maximize_window()
        usernameInput = self.browser.find_element(By.NAME, "username")
        passwordInput = self.browser.find_element(By.NAME, "password")
        usernameInput.send_keys(self.username)
        passwordInput.send_keys(self.password)
        passwordInput.send_keys(Keys.ENTER)
        time.sleep(10)

    def scroll_dialog(self):
        scroll_box = self.browser.find_element(By.CLASS_NAME, "x6nl9eh")
        last_height = 0
        retries = 0
        while True:
            self.browser.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_box)
            time.sleep(2)
            new_height = self.browser.execute_script("return arguments[0].scrollHeight", scroll_box)
            if new_height == last_height:
                retries += 1
                if retries > 3:
                    break
            else:
                retries = 0
            last_height = new_height

    def extract_usernames(self):
        dialog = self.browser.find_element(By.XPATH, "//div[@role='dialog']//div[2]")
        all_links = dialog.find_elements(By.XPATH, ".//a[contains(@href, '/')]")
        users = set()
        for link in all_links:
            href = link.get_attribute("href")
            if href and href.startswith("https://www.instagram.com/") and href.count("/") == 4:
                username = href.split("/")[-2]
                users.add(username)
        return sorted(users)

    def get_list(self, list_type):
        self.browser.get(f"https://www.instagram.com/{self.username}/")
        time.sleep(5)
        if list_type == "followers":
            button = self.browser.find_element(By.XPATH, "//a[contains(@href, '/followers')]")
        else:
            button = self.browser.find_element(By.XPATH, "//a[contains(@href, '/following')]")
        button.click()
        time.sleep(3)
        self.scroll_dialog()
        return self.extract_usernames()

    def run(self):
        self.signIn()

        followers = self.get_list("followers")
        following = self.get_list("following")

        df_followers = pd.DataFrame(followers, columns=["Takipçiler"])
        df_following = pd.DataFrame(following, columns=["Takip Edilen"])

        # Farkları hesapla
        not_followed_back = sorted(list(set(followers) - set(following)))
        not_following_back = sorted(list(set(following) - set(followers)))

        df_not_followed_back = pd.DataFrame(not_followed_back, columns=["Takip Etmediğim Takipçiler"])
        df_not_following_back = pd.DataFrame(not_following_back, columns=["Geri Takip Etmeyenler"])

        with pd.ExcelWriter("instagram.xlsx", engine="openpyxl", mode="w") as writer:
            df_followers.to_excel(writer, sheet_name="Takipçiler", index=False)
            df_following.to_excel(writer, sheet_name="Takip Edilen", index=False)
            df_not_followed_back.to_excel(writer, sheet_name="Takip Etmediğim Takipçiler", index=False)
            df_not_following_back.to_excel(writer, sheet_name="Geri Takip Etmeyenler", index=False)

        print("✅ Tüm veriler instagram.xlsx dosyasına yazıldı.")

# Kullanım
insta = Instagram(username, password)
insta.run()