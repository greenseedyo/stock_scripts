#coding:utf-8
from Cookie import SimpleCookie

rawdata = 'fbm_402191899829086=base_domain=.www.nvesto.com; SERVERID=warrior; 2bd8f60281051886518bc3f76c3bc3b8=3c3714101face526965a289d0f75a04953374149a%3A4%3A%7Bi%3A0%3Bs%3A5%3A%2250700%22%3Bi%3A1%3Bs%3A10%3A%22Patrick+Lu%22%3Bi%3A2%3Bi%3A2592000%3Bi%3A3%3Ba%3A0%3A%7B%7D%7D; latestReferrer=https%3A%2F%2Fwww.facebook.com%2F; fbm_559107294212918=base_domain=.www.nvesto.com; PHPSESSID=uqjls7mlm8bc03ttq7rpjdf6e6; __utma=145157483.975940737.1497460598.1504286050.1504289564.10; __utmb=145157483.2.10.1504289564; __utmc=145157483; __utmz=145157483.1504196447.8.3.utmcsr=facebook.com|utmccn=(referral)|utmcmd=referral|utmcct=/; fbsr_559107294212918=PjTlweFBw54ebrPoOzm2l8NyC8gxnn4WOk3FIxo69mA.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImNvZGUiOiJBUUI0X3BSUEk1aU9rYWdLdmIxNzdic0xBZm91djlwS0NTS2NqNkM1a3l0N0tYWFBmd2RwZTFpUEtrWHd5cDVMcmxkcjRhSVgyQnVVUFJwa04zOWxBWHZydmo5UzdPQldxNzZnczRLYkJrSHZpX1AwMDlZX0VOWFBvNjY1clF1TE5mY01OYTNSRjBsVGQxZDc4Z19ULUFqZFZZaUFlcGhtTUlEbVcxc280eWlQVkhQUDZSV0NiS1JqYnpXazRSS2ZBd2RQdm1UdmI5cDZqRWxva1VFNUhPMWJyTWhUeUplSGh1NjBmOXVscGUxRXgwX0lkczR4c05ZRmhKbFhxQ3hYVmhMVDJabkw5Z0hzQ0FmbU9RTlBlUVlIOV9WNGt2UXN0NkZZLUhJR2xzQW9UeDlfOGJ6V3pZRXpNNlVtWi1ZelcyNDFMbWFMallwOVU5NzFWUm05b1hCMSIsImlzc3VlZF9hdCI6MTUwNDI4OTkwNSwidXNlcl9pZCI6IjEwMTU5Mjk5NzA4NTkwMjA0In0'
cookie = SimpleCookie()
cookie.load(rawdata)

# Even though SimpleCookie is dictionary-like, it internally uses a Morsel object
# which is incompatible with requests. Manually construct a dictionary instead.
cookies = {}
for key, morsel in cookie.items():
    cookies[key] = morsel.value

import requests
data = {}
url = "https://www.nvesto.com/tpe/2610/majorforce#!/fromdate/2017-08-31/todate/2017-08-31/view/summary"
print requests.get(url, data=data, cookies=cookies).text
