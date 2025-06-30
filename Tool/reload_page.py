from rich.console import Console
from rich.live import Live
from rich.table import Table
import concurrent.futures
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from threading import Lock

IP_LIST = [
    "10.11.25.102",
    "10.11.25.36",
]

RELOAD_COUNT = 10

logs = {ip: [] for ip in IP_LIST}
log_lock = Lock()
console = Console()


def is_alive(ip):
    try:
        response = requests.get(f"http://{ip}/io/admin/version_int/value.json", timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def setup_driver(ip):
    options = Options()
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-logging")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    options.page_load_strategy = "eager"
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(f"http://{ip}/io/")
        return driver
    except WebDriverException as e:
        append_log(ip, f"[red]❌ [{ip}]: WebDriver error: {e}[/red]")
        return None


def append_log(ip, message):
    with log_lock:
        logs[ip].append(message)


def render_table():
    table = Table(title="IP Testing Progress", expand=True)
    for ip in IP_LIST:
        table.add_column(ip, style="cyan")

    max_rows = max(len(logs[ip]) for ip in IP_LIST)
    for i in range(max_rows):
        row = []
        for ip in IP_LIST:
            row.append(logs[ip][i] if i < len(logs[ip]) else "")
        table.add_row(*row)

    return table


def test_ip(ip):
    if not is_alive(ip):
        append_log(ip, f"[red]❌ [{ip}]: Device not responding[/red]")
        return

    driver = setup_driver(ip)
    if not driver:
        return

    for i in range(RELOAD_COUNT):
        if not is_alive(ip):
            append_log(ip, f"[red]❌ [{ip}]: Device lost at reload {i+1}[/red]")
            return
        driver.refresh()
        append_log(ip, f"[green]✅ Reload {i+1}/{RELOAD_COUNT}[/green]")
        time.sleep(2)

    append_log(ip, f"[bold green]🎉 [{ip}]: Test complete[/bold green]")
    driver.quit()
    append_log(ip, "[yellow]🔻 Driver closed[/yellow]")


def main():
    with Live(render_table(), refresh_per_second=4) as live:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(IP_LIST)) as executor:
            futures = [executor.submit(test_ip, ip) for ip in IP_LIST]

            while not all(f.done() for f in futures):
                live.update(render_table())
                time.sleep(0.5)

            live.update(render_table())  # final render


if __name__ == "__main__":
    main()
