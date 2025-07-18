import os
import json
import time
from urllib.parse import urlparse
from PIL import Image
import base64
import requests
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def get_dict_md5(d):
    h = hashlib.md5()
    for key, value in d.items():
        h.update(str(key).encode('utf-8'))
        h.update(str(value).encode('utf-8'))
    return h.hexdigest()



def get_screenshot(url, width, height, timeout, real_time_out, host_dir, full_page):
    print("正在初始化浏览器")
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # 使用新版 headless 模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('lang=zh_CN.UTF-8')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # 添加139px的UI高度
    height += 139 

    try:
        print("正在设置窗口大小：", url)
        driver.set_window_size(width, height)
        driver.get(url)

        print("等待网页加载")
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        time.sleep(real_time_out)

        now_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        final_pic_file = os.path.join(host_dir, f"{now_time}.png")
        final_lastest_file = os.path.join(host_dir, "lastest.png")

        total_height = driver.execute_script("""
            return Math.max(
                document.body.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.clientHeight,
                document.documentElement.scrollHeight,
                document.documentElement.offsetHeight
            );
        """)

        if full_page != 0:
            # 3
            if full_page == 3:
                print("｜！！！！！｜采用设备模拟截图模式")
                driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                    'mobile': False,
                    'width': width,
                    'height': total_height,
                    'deviceScaleFactor': 1
                })
                res = driver.execute_cdp_cmd('Page.captureScreenshot', {'fromSurface': True})
                img_data = base64.b64decode(res['data'])
                # with open(final_pic_file, 'wb') as f:
                #     f.write(img_data)
                with open(final_lastest_file, 'wb') as f:
                    f.write(img_data)
                return final_pic_file, final_lastest_file
            # 1
            if full_page == 1:
                print("｜！！！！！｜采用拉高视窗截图模式")
                driver.set_window_size(width, total_height)
                driver.execute_script(f"window.scrollTo(0, {total_height});")
            else:
            # 2    
                print("｜！！！！！｜不进行任何滚动，直接截图")
            # 2
            # driver.save_screenshot(final_pic_file)
            driver.save_screenshot(final_lastest_file)
            return final_pic_file, final_lastest_file
        # 0
        print("｜！！！！！｜采用滚动截图模式")
        scrolled_height = 0
        next_scrolled_height = 0
        image_path_list = []

        print("页面总高度：", total_height)
        page = 1
        while next_scrolled_height < total_height:
            driver.execute_script(f"window.scrollTo(0, {next_scrolled_height});")
            next_scrolled_height += height
            if total_height - scrolled_height < height:
                next_scrolled_height = total_height
            print(f"正在截图 [{page}]：{scrolled_height} - {next_scrolled_height}")
            time.sleep(real_time_out)

            pic_file = os.path.join(host_dir, f"{now_time}|{scrolled_height}_{next_scrolled_height}.png")
            driver.save_screenshot(pic_file)
            image_path_list.append(pic_file)
            scrolled_height += height
            page += 1

        # 合并截图
        images = [Image.open(p) for p in image_path_list]
        for i in range(len(images)):
            if i == len(images) - 1:
                overlap = scrolled_height - total_height
                if overlap > 0:
                    images[i] = images[i].crop((0, overlap, images[i].width, height))
            else:
                images[i] = images[i].crop((0, 0, images[i].width, height))

        stitched_image = Image.new("RGB", (width, total_height))
        for i, img in enumerate(images):
            stitched_image.paste(img, (0, i * height))

        stitched_image.save(final_pic_file)
        stitched_image.save(final_lastest_file)
        print("截图成功")
        return final_pic_file, final_lastest_file
    
    except Exception as e:
        print(f"发生错误: {e}")
        return None, None

    finally:
        driver.quit()


if __name__ == "__main__":
    # 读取list.json文件
    with open("list.json", "r") as f:
        data = json.load(f)

    # # 导入友链信息
    # try:
    #     print("正在获取友链信息")
    #     response = requests.get("https://blog.hzchu.top/data/friends.json")
    #     if response.status_code != 200:
    #         print("请求失败")
    #     friends_data = response.json()["friends"]
    #     # 遍历友链信息
    #     for i in friends_data:
    #         url = i[1]
    #         data.append({
    #             "url": url,
    #             "timeout": 30,
    #             "width": 1050,
    #             "height": 700,
    #             "real_time_out": 10,
    #             "full_page": 2,
    #         })

    # except Exception as e:
    #     print(f"发生错误: {e}")

    for i in data:
        print("开始截图：", i["url"])
        # 算出 i 的 md5 值
        # i_hash = get_dict_md5(i)
        # 获取url
        url = i["url"]
        timeout = i["timeout"]
        # 获取宽度和高度
        width = i["width"]
        height = i["height"]
        real_time_out = i["real_time_out"]
        full_page = i["full_page"]
        # 写入文件
        host = urlparse(url).netloc
        host_dir = os.path.join("save", host)
        if not os.path.exists(host_dir):
            os.mkdir(host_dir)
        get_screenshot(url, width, height, timeout, real_time_out, host_dir, full_page)