---
name: weather-query
description: Query weather information for Chinese cities using playwright-cli. Invoke when user asks about weather, temperature, or what to wear based on weather conditions in China.
---

# 天气查询 (Weather Query)

## 使用方法

当用户询问天气、温度、是否需要带伞、该穿什么衣服等与天气相关的问题时，自动使用此技能。

## 操作步骤

### 1. 打开浏览器并导航到目标城市天气页面

```bash
npx playwright-cli open "https://www.weather.com.cn/weather/101300301.shtml"
```

> **重要**: 必须先执行 `open` 命令打开浏览器，直接使用 `goto` 会报错 "The browser 'default' is not open"

### 2. 获取天气数据

一次性获取温度、天气状况和风力信息：

```bash
npx playwright-cli eval "() => { const temp = document.querySelector('.tem'); const weather = document.querySelector('.wea'); const wind = document.querySelector('.win'); return { temperature: temp ? temp.innerText : null, weather: weather ? weather.innerText : null, wind: wind ? wind.innerText : null }; }"
```

### 3. 关闭浏览器

```bash
npx playwright-cli close
```

> **重要**: 查询完成后务必关闭浏览器释放资源

## 中国城市代码参考

| 城市 | URL 代码 | 城市 | URL 代码 |
|------|----------|------|----------|
| 北京 | 101010100 | 武汉 | 101200101 |
| 上海 | 101020100 | 杭州 | 101210101 |
| 广州 | 101280101 | 西安 | 101110101 |
| 深圳 | 101280601 | 南京 | 101190101 |
| 成都 | 101270101 | 长沙 | 101250101 |
| 重庆 | 101040000 | 合肥 | 101220101 |
| 天津 | 101030100 | 沈阳 | 101070101 |
| 哈尔滨 | 101050101 | 长春 | 101060101 |
| 石家庄 | 101090101 | 太原 | 101100101 |
| 济南 | 101120101 | 郑州 | 101180101 |
| 青岛 | 101120201 | 南昌 | 101240101 |
| 大连 | 101070201 | 福州 | 101230101 |
| 厦门 | 101230201 | 贵阳 | 101260101 |
| 昆明 | 101290101 | 南宁 | 101300101 |
| 拉萨 | 101140101 | 乌鲁木齐 | 101130101 |
| 兰州 | 101160101 | 包头 | 101080201 |
| 银川 | 101170101 | 呼和浩特 | 101080101 |
| **柳州** | **101300301** | **鹿寨** | **101300304** |

## 区县天气查询

如果查询的区县（如鹿寨、融安等）不在城市代码列表中：

1. 通过网络搜索 `site:weather.com.cn 区县名 天气` 查找对应的天气页面
2. 或访问 `https://m.weather.com.cn/mweather/区县名.shtml` 尝试
3. 找到对应的 URL 后，从 URL 中提取城市代码（如 `101300304`）

## CSS 选择器说明

- `.tem` - 温度（返回格式：23℃）
- `.wea` - 天气状况（返回格式：阴、晴、雨等）
- `.win` - 风力信息（返回格式：<3级）

## 示例输出

执行 eval 命令后会返回 JSON 格式数据：

```json
{
  "temperature": "23℃",
  "weather": "阴",
  "wind": "<3级"
}
```

解读为：
```
🌡️ 温度: 23℃
☁️ 天气: 阴
💨 风力: <3级
```

## 完整命令示例

查询柳州天气：

```bash
npx playwright-cli open "https://www.weather.com.cn/weather/101300301.shtml"
npx playwright-cli eval "() => { const temp = document.querySelector('.tem'); const weather = document.querySelector('.wea'); const wind = document.querySelector('.win'); return { temperature: temp ? temp.innerText : null, weather: weather ? weather.innerText : null, wind: wind ? wind.innerText : null }; }"
npx playwright-cli close
```

## 注意事项

1. **必须先执行 `open` 命令** - 直接使用 `goto` 会报错 "The browser 'default' is not open"
2. **必须使用中国天气网** - weather.com.cn 对中国城市支持好，weather.com 支持差
3. **查询完成后务必关闭浏览器** - 使用 `npx playwright-cli close`
4. **区县需要单独查找代码** - 通过网络搜索找到对应的天气页面 URL，从中提取城市代码
5. **控制台可能有 PSReadLine 错误** - Windows PowerShell 的 PSReadLine 插件偶发错误，但不影响命令执行结果
6. **如果选择器返回 `null`** - 说明页面结构可能变化，需要更新选择器
