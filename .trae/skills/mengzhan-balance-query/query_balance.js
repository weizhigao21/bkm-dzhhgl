async page => {
  const response = await page.evaluate(async () => {
    const resp = await fetch('https://www.mengzhan28.xyz/api/v1/financelog/getBalanceByUid', {
      method: 'POST',
      headers: {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjc3NzcsIlRva2VuVHlwZSI6MCwiaXNzIjoiYWxuaXRhayIsImV4cCI6MTc3NjQ4NDUwMiwiaWF0IjoxNzc1ODc5NzAyfQ.do0mtDSU0sqK7arrGaDtT5QiSQtqpCV3c8zOXobE-OQ',
        'content-length': '0',
        'origin': 'https://www.mengzhan28.xyz',
        'priority': 'u=1, i',
        'referer': 'https://www.mengzhan28.xyz/account/wealth',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sign': '614dfb7be5d1e8850a77a1005ce7b48a01d4604c',
        'sign-nonce': 'mex2regmzj'
      },
      body: ''
    });
    return await resp.json();
  });
  console.log(JSON.stringify(response));
  return response;
}
