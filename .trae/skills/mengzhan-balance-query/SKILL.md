---
name: "mengzhan-balance-query"
description: "Query mengzhan28.xyz user balance via API using playwright-cli. Invoke when user asks to check balance or query account balance on mengzhan28."
---

# Mengzhan28 Balance Query

Query user balance from mengzhan28.xyz using playwright-cli with proper sign generation and error handling.

## Sign Generation (Python)

```python
import random
import string
import hashlib

def generate_sign(url_path: str) -> tuple[str, str]:
    secret = "paUc3gO5btfZ7oBJ0ruAyW18TzN6m9Dk"
    nonce = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    sign = hashlib.sha1((nonce + url_path + secret).encode()).hexdigest()
    return nonce, sign
```

## API Details

- **URL**: `https://www.mengzhan28.xyz/api/v1/financelog/getBalanceByUid`
- **Method**: POST
- **Path**: `/api/v1/financelog/getBalanceByUid`

## Required Headers

| Header | Value |
|--------|-------|
| accept | application/json, text/plain, */* |
| accept-language | zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6 |
| authorization | Bearer token (user-specific, required) |
| content-length | 0 |
| origin | https://www.mengzhan28.xyz |
| priority | u=1, i |
| referer | https://www.mengzhan28.xyz/account/wealth |
| sec-ch-ua | "Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145" |
| sec-ch-ua-mobile | ?0 |
| sec-ch-ua-platform | "Windows" |
| sec-fetch-dest | empty |
| sec-fetch-mode | cors |
| sec-fetch-site | same-origin |
| sign | Generated SHA1 hash |
| sign-nonce | 10-char random string |

## Complete Workflow (Optimized)

### Step 1: Generate Sign and Query Script

First, generate a fresh sign and create the query script in one step:

```bash
# Generate sign
python -c "import random,string,hashlib; nonce=''.join(random.choices(string.ascii_lowercase+string.digits,k=10)); sign=hashlib.sha1((nonce+'/api/v1/financelog/getBalanceByUid'+'paUc3gO5btfZ7oBJ0ruAyW18TzN6m9Dk').encode()).hexdigest(); print(f'nonce: {nonce}'); print(f'sign: {sign}')"
```

### Step 2: Open Browser AND Run Query in Sequence

**IMPORTANT**: Always open browser first before running query, otherwise it will fail with "browser is not open" error.

```bash
# 2.1 Open browser first (REQUIRED)
playwright-cli open https://www.mengzhan28.xyz --browser=msedge

# 2.2 Then run query (after browser is open, script is in skills folder)
playwright-cli run-code --filename .trae/skills/mengzhan-balance-query/query_balance.js
```

## Query Script Template

The `query_balance.js` file should contain:

```javascript
async page => {
  const response = await page.evaluate(async () => {
    const resp = await fetch('https://www.mengzhan28.xyz/api/v1/financelog/getBalanceByUid', {
      method: 'POST',
      headers: {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'authorization': 'Bearer token_here',
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
        'sign': 'generated_sign_here',
        'sign-nonce': 'generated_nonce_here'
      },
      body: ''
    });
    return await resp.json();
  });
  console.log(JSON.stringify(response));
  return response;
}
```

## Response Format

Success response (code: 200):
```json
{
  "code": 200,
  "data": {
    "data": {
      "ID": 619655,
      "CreatedAt": "2024-10-20T12:54:58+08:00",
      "UpdatedAt": "2026-04-13T22:51:36+08:00",
      "Uid": 7777,
      "Balance": 219,
      "FreezeBalance": 0,
      "Score": 0,
      "FreezeScore": 0
    },
    "leave": 1
  },
  "msg": "ok"
}
```

Error response (code: 400):
```json
{"code": 400, "msg": "非法请求"}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "browser 'default' is not open" | Browser not opened before query | Run `playwright-cli open` first, then query |
| code: 400 "非法请求" | Sign validation failed | Regenerate sign with correct nonce and hash |
| Authorization error | Token expired or missing | Obtain fresh authorization token |
| Network error | Connection issue | Check network and retry |
| Empty response | CORS blocked | Ensure request from correct origin |

## Important Notes

1. **Order Matters**: Always open browser BEFORE running query command - this is the most common mistake
2. **Sign Changes**: Each request requires a new sign (nonce + sign pair)
3. **Authorization Token**: Has expiration, may need renewal
4. **Browser Context**: Cookies and context persist in playwright session
5. **Long Commands**: Use `--filename` option to avoid command-line length issues with `run-code`
