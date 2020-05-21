import os, sys
import time
import json
import random
import concurrent.futures
import logging
import codecs

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

from datetime import datetime
from datetime import timezone

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

from selenium.webdriver import ChromeOptions

sys.path.append('..')


class FoodyDataFeed:
    def __init__(self, blob):
        self.blob = str(blob)
        self.base_url = 'https://www.foody.vn/ho-chi-minh/' + self.blob
        self.opts = ChromeOptions()
        # Uncomment these option if dont want to see the browser or deploy on linux server.
        # self.opts.add_argument('--headless')
        # self.opts.add_argument('--no-sandbox')
        # self.opts.add_argument('--disable-dev-shm-usage')
        # self.opts.add_argument("--window-size=2560,1440")
        self.opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36")
        self.driver = webdriver.Chrome(options=self.opts)
        self.driver1 = webdriver.Chrome(options=self.opts)
        self.driver2 = webdriver.Chrome(options=self.opts)
        # self.list_url = []
        # self.ts = []
        # self.filename = 'Foody_tmp_{}'.format(datetime.now())

    def parse_restaurant(self, menu_url):
        """Get profile info of ones foody restaurant
        :input: link/links to foody profiles
        :output: A Json formatted file example in this git.
        """

        self.driver1.get(menu_url)
        if self.driver1.execute_script('return document.readyState;'):
            time.sleep(3)
        time.sleep(5)
        promotion_info = self.driver1.find_element_by_css_selector('div.promotion-item > div.content').text
        menu_arr = []
        element = WebDriverWait(self.driver1, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "name-restaurant"))
        )
        restaurant_name = element.text
        restaurant_add = self.driver1.find_element_by_class_name('address-restaurant').text
        restaurant_number_rating = self.driver1.find_element_by_class_name('number-rating').text
        restaurant_cost_range = self.driver1.find_element_by_class_name('cost-restaurant').text
        restaurant_open_time = self.driver1.find_element_by_css_selector('i.fa-clock').text

        for elem in self.driver1.find_elements_by_class_name("item-restaurant-row"):
            # with open("Output.html", "w") as text_file:
            #     print(f"{elem.get_attribute('innerHTML')}", file=text_file)

            food_item_name = elem.find_element_by_class_name('item-restaurant-name').text
            try:
                food_item_desc = elem.find_element_by_class_name('item-restaurant-desc').text
            except NoSuchElementException:
                food_item_desc = None
            food_item_price = elem.find_element_by_class_name('current-price').text
            try:
                food_image_link = elem.find_element_by_tag_name('img').get_attribute('src')
            except NoSuchElementException:
                food_image_link = None

            food_item = {
                "food_item_name": food_item_name,
                "food_item_desc": food_item_desc,
                "food_item_price": food_item_price,
                "food_image_link": food_image_link,
            }
            menu_arr.append(food_item)

        restaurant_info_json = {
            "restaurant_info": [{
                "restaurant_name": restaurant_name,
                "restaurant_add": restaurant_add,
                "restaurant_open_time": restaurant_open_time,
                "restaurant_cost_range": restaurant_cost_range,
                "restaurant_number_rating": restaurant_number_rating,
                "promotion_info": promotion_info,
                "menu": menu_arr,
            }]
        }
        with codecs.open('restaurant_info_json_data_compatibility.json', 'w', encoding='utf-8') as f:
            json.dump(restaurant_info_json, f)

        with codecs.open('restaurant_info_json_data_easy_read.json', 'w', encoding='utf-8') as f:
            json.dump(restaurant_info_json, f, ensure_ascii=False, indent=4)

        logging.info(restaurant_info_json)

        self.driver1.close()

        logging.info("End restaurant info")

    def parse_profile(self, profile_links):
        """Get profile info of ones foody user
        :input: link/links to foody profiles
        :output: A Json formatted file example in this git.
        """

        user_info_arr = []

        for profile_link in profile_links:
            self.driver2.get(profile_link)

            user_link = profile_link
            try:
                user_name = self.driver2.find_element_by_css_selector("a.ru-username").text
            except NoSuchElementException:
                user_name = None
            # https://stackoverflow.com/questions/20986631/

            SCROLL_PAUSE_TIME = 0.5
            SCROLL_END = 0

            # Get scroll height
            last_height = self.driver2.execute_script("return document.body.scrollHeight")

            while True:
                # Scroll down to bottom
                self.driver2.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                #     (By.CSS_SELECTOR, "a.fd-btn-more"))).click()
                try:
                    load_more_btn = self.driver2.find_element_by_class_name("fd-btn-more")
                    self.driver.execute_script("arguments[0].click();", load_more_btn)
                except StaleElementReferenceException:
                    time.sleep(3)
                    try:
                        load_more_btn = self.driver2.find_element_by_class_name("fd-btn-more")
                        self.driver.execute_script("arguments[0].click();", load_more_btn)
                    except StaleElementReferenceException:
                        break
                except NoSuchElementException:
                    break
                # Wait to load page
                time.sleep(SCROLL_PAUSE_TIME)

                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver2.execute_script("return document.body.scrollHeight")

                if new_height == last_height:
                    break
                last_height = new_height
                SCROLL_END += 1
                if SCROLL_END == 20:
                    break

            user_review_info = []
            for user_review in self.driver2.find_elements_by_class_name("review-item"):
                reviewed_restaurant_name = user_review.find_element_by_css_selector("a.rr-name").text
                reviewed_restaurant_link = user_review.find_element_by_css_selector("a.rr-name").get_attribute("href")
                reviewed_restaurant_device = \
                user_review.find_element_by_css_selector("a.ru-device").text.strip().split(" ")[1]
                reviewed_restaurant_time = user_review.find_element_by_css_selector("span.ru-time").text
                try:
                    reviewed_restaurant_viewed = user_review.find_element_by_css_selector(
                        "div.review-statistic > span.ng-scope").text
                except NoSuchElementException:
                    reviewed_restaurant_viewed = None
                try:
                    reviewed_restaurant_title = user_review.find_element_by_css_selector("a.rd-title").text
                except NoSuchElementException:
                    reviewed_restaurant_title = None

                try:
                    reviewed_restaurant_detail = user_review.find_element_by_css_selector("div.rd-des span").text
                except NoSuchElementException:
                    reviewed_restaurant_detail = None

                reviewed_restaurant_option = []
                reviewed_restaurant_commented = []
                reviewed_restaurant_image = []
                try:
                    for link in user_review.find_elements_by_css_selector("img.rp-lazy-load"):
                        reviewed_restaurant_image.append(link.get_attribute("src"))
                except NoSuchElementException:
                    reviewed_restaurant_image = None

                try:
                    for comment in user_review.find_elements_by_css_selector("div.fc-right"):
                        reviewed_restaurant_commented_name = comment.find_element_by_css_selector("a.fc-username").text
                        reviewed_restaurant_commented_link = comment.find_element_by_css_selector(
                            "a.fc-username").get_attribute("href")
                        reviewed_restaurant_commented_detail = comment.find_element_by_css_selector(
                            "span.fc-user-comment").text
                        reviewed_restaurant_commented_time = comment.find_element_by_css_selector("div.ng-binding").text
                        reviewed_restaurant_commented_json_info = {
                            "reviewed_restaurant_commented_name": reviewed_restaurant_commented_name,
                            "reviewed_restaurant_commented_link": reviewed_restaurant_commented_link,
                            "reviewed_restaurant_commented_detail": reviewed_restaurant_commented_detail,
                            "reviewed_restaurant_commented_time": reviewed_restaurant_commented_time,
                        }

                        reviewed_restaurant_commented.append(reviewed_restaurant_commented_json_info)
                except NoSuchElementException:
                    reviewed_restaurant_commented = None

                try:
                    for opt in user_review.find_elements_by_css_selector("div.review-options span"):
                        reviewed_restaurant_option.append(opt.text)
                        reviewed_restaurant_text = " ".join(reviewed_restaurant_option)
                        reviewed_restaurant_option = reviewed_restaurant_text

                except NoSuchElementException:
                    reviewed_restaurant_option = None

                user_review = {
                    "reviewed_restaurant_name": reviewed_restaurant_name,
                    "reviewed_restaurant_link": reviewed_restaurant_link,
                    "reviewed_restaurant_device": reviewed_restaurant_device,
                    "reviewed_restaurant_time": reviewed_restaurant_time,
                    "reviewed_restaurant_viewed": reviewed_restaurant_viewed,
                    "reviewed_restaurant_title": reviewed_restaurant_title,
                    "reviewed_restaurant_detail": reviewed_restaurant_detail,
                    "reviewed_restaurant_option": reviewed_restaurant_option,
                    "reviewed_restaurant_commented": reviewed_restaurant_commented,
                    "reviewed_restaurant_image": reviewed_restaurant_image,
                }

                user_review_info.append(user_review)

            user_tmp = {
                "user_info": [{
                    "user_name": user_name,
                    "user_link": user_link,
                    "user_review": user_review_info,
                }
                ]
            }
            user_info_arr.append(user_tmp)

            try:
                with codecs.open('user_tmp_backup_data.json', encoding='utf-8') as json_file:
                    data = json.load(json_file)

                    tmp = data["user_info_tmp"]

                    tmp.append(user_tmp)

                with codecs.open('user_tmp_backup_data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)

            except FileNotFoundError:
                with open('user_tmp_backup_data.json', 'w', encoding='utf-8') as f:
                    json.dump(user_tmp, f, indent=4)

        user_output_json = {
            "userInfoOutPut": user_info_arr
        }

        with codecs.open('user_output_json_data_compatibility.json', 'w', encoding='utf-8') as f:
            json.dump(user_output_json, f)

        with codecs.open('user_output_json_data_easy_read.json', 'w', encoding='utf-8') as f:
            json.dump(user_output_json, f, ensure_ascii=False, indent=4)

        self.driver2.close()

    def crawl(self):
        self.driver.get(self.base_url)
        time.sleep(3)
        if self.driver.execute_script('return document.readyState;'):
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "view-all-menu"))
            )
            try:
                menu_url = element.find_element_by_tag_name('a').get_attribute('href')
            except StaleElementReferenceException:
                time.sleep(3)
                menu_url = self.driver.find_element_by_class_name("view-all-menu").find_element_by_tag_name(
                    'a').get_attribute('href')
            self.parse_restaurant(menu_url)

        restaurant_name = self.driver.find_element_by_class_name("main-info-title").find_element_by_tag_name('h1').text
        restaurant_cuisines = self.driver.find_elements_by_css_selector("a.microsite-cuisine")
        cuisines = []
        for cuisine in restaurant_cuisines:
            cuisines.append(cuisine.text)
        restaurant_category = self.driver.find_element_by_css_selector("div.category-items a").text
        restaurant_audiences = self.driver.find_element_by_css_selector("div.audiences").text.strip()

        self.driver.find_element_by_css_selector("div.micro-main-menu > div > div > ul > li:nth-child(4) > a").click()

        # https://stackoverflow.com/questions/20986631/
        SCROLL_PAUSE_TIME = 0.5

        # Get scroll height
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
            #     (By.CSS_SELECTOR, "a.fd-btn-more"))).click()
            try:
                load_more_btn = self.driver.find_element_by_class_name("fd-btn-more")

                self.driver.execute_script("arguments[0].click();", load_more_btn)
            except NoSuchElementException:
                break
            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break
            last_height = new_height

        review_info_restaurant = []
        parse_profile_arr = []

        for review in self.driver.find_elements_by_class_name("review-item"):

            profile_link = review.find_element_by_css_selector("a.ru-username").get_attribute('href')
            profile_image_link = review.find_element_by_tag_name('img').get_attribute('src')
            profile_review_time = review.find_element_by_css_selector("span.ru-time").text
            review_device = review.find_element_by_css_selector("a.ru-device").text.strip().split(" ")[1]
            review_title = review.find_element_by_css_selector("a.rd-title").text
            review_link = review.find_element_by_css_selector("a.rd-title").get_attribute('href')

            try:
                review_detail = review.find_element_by_class_name("rd-des").find_element_by_tag_name('span').text
            except NoSuchElementException:
                review_detail = None

            try:
                if review.find_element_by_class_name("review-not-foody"):
                    review_of_foody = 0
                else:
                    review_of_foody = 1
            except NoSuchElementException:
                review_of_foody = 1

            review_info = {
                "profile_link": profile_link,
                "profile_image_link": profile_image_link,
                "profile_review_time": profile_review_time,
                "review_link": review_link,
                "review_title": review_title,
                "review_device": review_device,
                "review_detail": review_detail,
                "review_of_foody": review_of_foody,
            }

            review_info_restaurant.append(review_info)

            parse_profile_arr.append(profile_link)

        review_json = {
            "review": [{
                "restaurant_url": self.base_url,
                "restaurant_name": restaurant_name,
                "cuisines": cuisines,
                "restaurant_category": restaurant_category,
                "restaurant_audiences": restaurant_audiences,
                "review_info": review_info_restaurant,
            }
            ]
        }

        with codecs.open('review_info_json_data_compatibility.json', 'w', encoding='utf-8') as f:
            json.dump(review_json, f)

        with codecs.open('review_info_json_data_easy_read.json', 'w', encoding='utf-8') as f:
            json.dump(review_json, f, ensure_ascii=False, indent=4)

        self.parse_profile(parse_profile_arr)
        self.driver.close()


if __name__ == '__main__':
    # add keyword to get data of another restaurant
    # concurrent will added as requested personal.
    # caching is another issue need to concern.
    # json output for simplify.

    """https://www.foody.vn/ho-chi-minh/chao-restaurant"""
    keyword = ["chao-restaurant"]
    f = FoodyDataFeed(blob=keyword[0])
    f.crawl()
