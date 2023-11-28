import requests,json,urllib.parse,re,os,threading
from lxml import etree
import pandas as pd
import get_proxy
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



class spider_CNKI(threading.Thread):

    def __init__(self,proxy,name_list,j) -> None:
        self.proxy = proxy
        self.name_list = name_list
        self.j = j
        super().__init__()

    def creatbody_search(self,value):
        # 修改步骤一的body
        data = "searchStateJson=%7B%22StateID%22%3A%22%22%2C%22Platfrom%22%3A%22%22%2C%22QueryTime%22%3A%22%22%2C%22Account%22%3A%22knavi%22%2C%22ClientToken%22%3A%22%22%2C%22Language%22%3A%22%22%2C%22CNode%22%3A%7B%22PCode%22%3A%22JOURNAL%22%2C%22SMode%22%3A%22%22%2C%22OperateT%22%3A%22%22%7D%2C%22QNode%22%3A%7B%22SelectT%22%3A%22%22%2C%22Select_Fields%22%3A%22%22%2C%22S_DBCodes%22%3A%22%22%2C%22QGroup%22%3A%5B%7B%22Key%22%3A%22subject%22%2C%22Logic%22%3A1%2C%22Items%22%3A%5B%5D%2C%22ChildItems%22%3A%5B%7B%22Key%22%3A%22txt%22%2C%22Logic%22%3A1%2C%22Items%22%3A%5B%7B%22Key%22%3A%22txt_1%22%2C%22Title%22%3A%22%22%2C%22Logic%22%3A1%2C%22Name%22%3A%22TI%22%2C%22Operate%22%3A%22%25%22%2C%22Value%22%3A%22'"+urllib.parse.quote(value)+"'%22%2C%22ExtendType%22%3A0%2C%22ExtendValue%22%3A%22%22%2C%22Value2%22%3A%22%22%7D%5D%2C%22ChildItems%22%3A%5B%5D%7D%5D%7D%5D%2C%22OrderBy%22%3A%22OTA%7CDESC%22%2C%22GroupBy%22%3A%22%22%2C%22Additon%22%3A%22%22%7D%7D&displaymode=1&pageindex=1&pagecount=21&index=&searchType=%E5%88%8A%E5%90%8D(%E6%9B%BE%E7%94%A8%E5%88%8A%E5%90%8D)&clickName=&switchdata=search"
        return data
    
    def get_value(self,name):
        # 创建session,启动代理
        spider_session = requests.Session()
        # spider_session.proxies = self.proxy
        headers = {
            "Host": "navi.cnki.net",
            "Connection": "keep-alive",
            "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            "Accept": "text/plain, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua-mobile": "?0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9"}
        
        # 获取cookies
        url_main = 'https://navi.cnki.net/knavi/'
        try:
            spider_session.get(url=url_main, headers=headers, verify=False)
        except:
            return
        # 获取期刊主页URL-搜索body格式

        # # 修改body
        if not os.path.exists('./{}'.format(name)):
            os.makedirs('./{}'.format(name))
        postbody = self.creatbody_search(name)

        # 检索
        url_search = 'https://navi.cnki.net/knavi/journals/searchbaseinfo'
        response = spider_session.post(url=url_search, headers=headers, data=postbody, verify=False)
        etree_search = etree.HTML(response.text)
        try:
            url_journal = etree_search.xpath("/html/body/div[1]/div[2]/ul/li/a/@href")[1]
            url_journal_key = re.findall("baseid=(.*)",url_journal)[0]
        except:
            print(name+'在知网中根本搜不到！')
            return

        # 访问一下期刊主页获取具体年份的URL
        url_journal = "https://navi.cnki.net/knavi/journals/{}/detail?uniplatform=NZKPT".format(url_journal_key)
        url_journalyear = "https://navi.cnki.net/knavi/journals/{}/yearList?pIdx=0".format(url_journal_key)
        headers['Referer'] = url_journal
        response = spider_session.get(url=url_journalyear, headers=headers, verify=False)
        etree_journal = etree.HTML(response.text)
        urllist_journal = etree_journal.xpath('//*[@id="2022_Year_Issue"]//a/@value')
        url_articl = [];name_articl = [];url_json = {}

        try:
            for i in urllist_journal:
                url = 'https://navi.cnki.net/knavi/journals/{}/papers?yearIssue={}&pageIdx=0&pcode=CJFD,CCJD'.format(url_journal_key,i)
                response = spider_session.post(url=url,headers=headers,data=None,verify=False)
                et = etree.HTML(response.text)
                url_articl.extend(et.xpath('/html/body/div/div/dd/span[1]/a/@href'))
                name_articl.extend(et.xpath('/html/body/div/div/dd/span[1]/a/text()[1]'))
                # time.sleep(5)

            pass # 这里看url_artical里的url正不正确

            # 创建目录
            for i in range(len(name_articl)):
                url_json[name_articl[i]] = url_articl[i]

            with open("./目录合集/{}.json".format(name),"w+",encoding= 'utf-8') as f:
                    json.dump(url_json,f,ensure_ascii=False,indent=2)
        except:
            print("{}在目录创建中报错,寄！".format(name))
            return
        
        # 更新headers
        headers = {
            "Host": "kns.cnki.net",
            "Connection": "keep-alive",
            "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9"}
        
        cop = re.compile("[^\u4e00-\u9fa5^a-z^A-Z^0-9]") # 匹配不是中文、大小写、数字的其他字符
        # try:
        # check = self.j[name]
        for i in url_json:
            try:
                response = spider_session.get(url=url_json[i], headers=headers, verify=False)
                with open("./{}/{}.txt".format(name,cop.sub('', i)),"w+", encoding= 'utf-8') as f:
                    f.write(response.text)
                    print(i+"下载完毕")
                pass
            except:
                print(i+"下载失败")
        # except:
        #     print("{}在页面保存中报错,寄！".format(name))
        #     return



    def run(self):
        for i in self.name_list:
            self.get_value(i)

def getnamelist(path):
    df = pd.read_excel(path)
    return df["期刊名称"].values.tolist()

if __name__ == "__main__":
    
    # API接口，返回格式为json
    api_url = "https://dps.kdlapi.com/api/getdps/?secret_id=oj94f5j0plfdru5sis99&num=1&signature=przc65de1h947lj2vo44ofn2e7aj0izx&pt=1&dedup=1&format=json&sep=1"
    page_url = "https://www.cnki.net"

    # 用户名密码认证(私密代理/独享代理)
    username = "d4200392661"
    password = "ecwmp8sv"

    with open('需下载.json','r',encoding='utf-8') as fp:
        data = json.load(fp)
    namelist = list(data.keys())
    namelist = getnamelist('CSSCI期刊目录最新版.xlsx')

    num = 1 # 线程数
    proxnum = 2 # 每个线程使用列表长度
    print(len(namelist))
    for i in range(len(namelist)//(num*proxnum)):
        threadlist=[]
        # proxies01 = get_proxy.get_proxy(api_url, username, password, page_url)
        # spider01 = spider_CNKI(proxy=proxies01,name_list=namelist[i*num:i*num+proxnum])
        for j in range(num):
            proxies = get_proxy.get_proxy(api_url, username, password, page_url)
            # proxies = 1
            threadlist.append(spider_CNKI(proxy=proxies,name_list=namelist[i*num*proxnum+j*proxnum:i*num*proxnum+(j+1)*proxnum],j = data))
        for thr in threadlist:thr.start()
        for thr in threadlist:thr.join()

        print('第'+str(i)+'/'+str(len(namelist)//(num*proxnum))+'组--------OK')
    



        