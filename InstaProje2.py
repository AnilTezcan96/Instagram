from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import pandas as pd
from collections import defaultdict
from openpyxl import load_workbook
from kullanici import username, password

class Instagram:
    def __init__(self, username, password):
        self.browser = webdriver.Edge()
        self.username = username
        self.password = password
        self.likes_counter = defaultdict(int)
        self.all_likers = []

    def signIn(self):
        self.browser.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)
        self.browser.maximize_window()
        self.browser.find_element(By.NAME, "username").send_keys(self.username)
        self.browser.find_element(By.NAME, "password").send_keys(self.password + Keys.ENTER)
        time.sleep(10)

    def get_post_links(self):
        self.browser.get(f"https://www.instagram.com/{self.username}/")
        time.sleep(5)
        links = set()
        last_height = self.browser.execute_script("return document.body.scrollHeight")
        while True:
            hrefs = self.browser.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
            for href in hrefs:
                link = href.get_attribute("href")
                links.add(link)
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        return list(links)

    def scroll_likes_dialog(self, max_scrolls=100, delay=1.5):
        try:
            scroll_box = self.browser.find_element(By.XPATH, "//div[@role='dialog']//div[contains(@class, 'x6s0dn4')]")
            last_height = 0
            scroll_attempts = 0

            for _ in range(max_scrolls):
                self.browser.execute_script("arguments[0].scrollBy(0, 200);", scroll_box)
                time.sleep(delay)

                new_height = self.browser.execute_script("return arguments[0].scrollHeight", scroll_box)
                if new_height == last_height:
                    scroll_attempts += 1
                    if scroll_attempts > 3:
                        break
                else:
                    scroll_attempts = 0
                    last_height = new_height
        except Exception as e:
            print(f"Scroll işlemi başarısız: {e}")

    def extract_likers(self):
        try:
            user_elements = self.browser.find_elements(By.XPATH, "//a[contains(@href, '/')]/div/div/span")
            users = set()
            for elem in user_elements:
                username = elem.text.strip()
                if username:
                    users.add(username)
            return users
        except Exception as e:
            print(f"Kullanıcılar alınamadı: {e}")
            return set()

    def collect_likes(self):
        post_links = self.get_post_links()
        print(f"🖼 Toplam Gönderi: {len(post_links)}")
        for link in post_links:
            try:
                self.browser.get(link)
                time.sleep(3)
                like_button = self.browser.find_element(By.XPATH, "//section[2]//div/span/a/span")
                like_button.click()
                time.sleep(3)

                self.scroll_likes_dialog()
                users = self.extract_likers()

                self.all_likers.extend(users)
                for user in users:
                    self.likes_counter[user] += 1

                # Kapama
                try:
                    self.browser.find_element(By.XPATH, "//div[@role='dialog']//button").click()
                except:
                    pass

            except Exception as e:
                print(f"❌ Beğeni bilgisi alınamadı: {link} -> {e}")

    def run(self):
        self.signIn()
        self.collect_likes()

        # Gönderi Bilgisi
        df_raw = pd.DataFrame(self.all_likers, columns=["Takipçiler"])
        df_raw.to_excel("instagram_analiz.xlsx", sheet_name="Gönderi Bilgisi", index=False)

        # Takipçi Analizi
        df_summary = pd.DataFrame(self.likes_counter.items(), columns=["Kullanıcı", "Adet"])
        df_summary = df_summary.sort_values(by="Adet", ascending=False)

        # Takipçi bilgisi excel'den alınır
        try:
            takipci_df = pd.read_excel("instagram.xlsx", sheet_name="Takipçiler")
            takipciler = set(takipci_df["Takipçiler"].dropna().astype(str))
        except Exception as e:
            print(f"Takipçi dosyası okunamadı: {e}")
            takipciler = set()

        ghost_followers = sorted(takipciler - set(self.likes_counter.keys()))
        unfollowers = sorted(set(self.likes_counter.keys()) - takipciler)

        df_ghosts = pd.DataFrame(ghost_followers, columns=["Ghost Followers"])
        df_unfollowers = pd.DataFrame(unfollowers, columns=["UnFollowers"])

        with pd.ExcelWriter("instagram_analiz.xlsx", engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df_summary.to_excel(writer, sheet_name="Takipçi Analizi", index=False)
            df_ghosts.to_excel(writer, sheet_name="Ghost Followers", index=False)
            df_unfollowers.to_excel(writer, sheet_name="UnFollowers", index=False)

        print("✅ 'instagram_analiz.xlsx' dosyasına veriler başarıyla yazıldı.")

# Kullanım
insta = Instagram(username, password)
insta.run()