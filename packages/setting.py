USERNAME = '18061704989'
PASSWORD = '199706181613x'

LOGIN_URL = 'https://passport.bilibili.com/login?gourl=http://space.bilibili.com/383890843/fans/follow'
PRIZE_URL = 'https://www.bilibili.com/tag/434405/feed'

# UP主ID名称的CSS定位信息：
UPER_ID = '#app > div.change-content > div.feed-wrap > div > div:nth-child({num}) > div.main-content > p.user-name.fs-16.ls-0.d-i-block > a'

# 抽奖动态内容链接的CSS定位信息：
INFORMATION_LOCATION = '#app > div.change-content > div.feed-wrap > div > div:nth-child({num}}) > div.main-content > div.card-content > div.post-content > div > div.text.p-rel.description > a > div.content-ellipsis'

# 动态页面 文章内容定位
CONTENT_LOCATION = 'body > div.app-ctnr > div.ssr-content > main > section.main-section.p-relative.dp-i-block.v-top > div.article-content-ctnr.p-relative.border-box > article > div > div.discription'

# 判断是否已经成功登陆
JUDGE = '#app > div.bili-header-m.report-wrap-module.report-wrap-module > div > div.bili-wrapper.clearfix > div.nav-con.fr > ul > li:nth-child(3) > a'

# UP主“+关注”的CSS定位信息：
UPER_LOCATION = '#app > div.change-content > div.feed-wrap > div > div:nth-child({num}) > div.focus-btn.p-abs.c-pointer > div > p'

# 点赞定位
LIKE_LOCATION = '#app > div.change-content > div.feed-wrap > div > div:nth-child({num}) > div.main-content > div.button-bar.tc-slate > div:nth-child(3)'

# UP主重复关注提示框：
UPER_TIP = 'body > div.bp-popup-ctnr > div > div.dp-table-cell.bp-v-middle > div > div.popup-content-ctnr > div.popup-btn-ctnr.t-center > button.bl-button.panel-btn.bl-button--ghost.bl-button--size'

# “分享”的CSS信息：
SHARE_LOCATION = '#app > div.change-content > div.feed-wrap > div > div:nth-child({num}) > div.main-content > div.button-bar.tc-slate > div:nth-child(1)'

# “分享评论框”的CSS信息：
COMMENT_LOCATION = '#app > div.change-content > div.feed-wrap > div > div:nth-child({num}) > div.forw-area > div.forw-main > div.forw-send.f-clear > div.f-left.textarea-container > textarea'

# “转发”的CSS信息：
SUBMIT_LOCATION = '#app > div.change-content > div.feed-wrap > div > div:nth-child({num}) > div.forw-area > div.forw-main > div.forw-send.f-clear > div.f-left.textarea-container > div.comm-tool.f-clear > div.comm-submit.f-right'

# 建立一个字库
WORD = '1234567890qwertyuiopasdfghjklzxcvbnm'

