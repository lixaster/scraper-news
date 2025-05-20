import schedule
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from browser_hubeigov import browser_func as browser_func_hubei
from browser_renmin import browser_func as browser_func_renmin
from utils_func import load_config, setup_logging
from move_to_stars_via_api import process_stars_move

# 配置日志
logger = setup_logging()
# 读取 yaml 文件，获取配置信息

config = load_config()


# 定义并行爬取任务函数
def job_scraper():
    logger.info("开始执行任务")
    process_stars_move()

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_hubei = executor.submit(browser_func_hubei)
        future_renmin = executor.submit(browser_func_renmin)

        results = [
            future.result() for future in as_completed([future_hubei, future_renmin])
        ]

    return all(results)


if __name__ == "__main__":
    try:
        if config.get("notify_switch", False):
            # 引入通知模块
            logger.info("通知功能已启用")
        else:
            logger.info("通知功能未启用")

        if config.get("debug_mode", False):
            logger.info("调试模式已开启")
            success_flag = job_scraper()
            if success_flag:
                logger.info("首次请求成功")
            else:
                logger.error("首次请求失败")

        # 设置每天的执行时间
        scheduletime = config.get("SCHEDULE_TIME", ["08:00"])
        interval = config.get("INTERVAL", 600)  # 单位：秒

        # 定义定时任务，如果 schedule_time 为多个时间组成的列表，则分别在每个时间点执行一次
        if not isinstance(scheduletime, list):
            scheduletime = [scheduletime]

        for every_time in scheduletime:
            schedule.every().day.at(every_time).do(job_scraper)

        logger.info(f"定时任务已设置，每天的 {scheduletime} 点执行一次")

        # 主循环
        while True:
            schedule.run_pending()
            time.sleep(interval)  # 每隔INTERVAL检查一次是否有任务需要执行
    except Exception as e:
        logger.error(f"主程序出错：{e}")
        exit(1)
