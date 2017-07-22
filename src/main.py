from bs4 import BeautifulSoup

def run():
    with open("../html/credit-20170722.htm") as f:
        html = BeautifulSoup(f)
    print(html)
    html.find_all()


if __name__ == "__main__":
    run()