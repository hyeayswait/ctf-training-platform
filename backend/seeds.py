"""预置 100 道示例题目 + 管理员账号。仅在数据库为空时执行一次。"""
from db import db, Challenge, User, Team
from werkzeug.security import generate_password_hash


# 格式：(title, category, difficulty, score, description, flag)
WEB = [
    ("备份文件泄露", "web", "easy", 100, "运维好像把源码备份忘在 Web 根目录了。提示：常见后缀 .bak .swp .zip", "flag{w3b_b4ckup_l3ak}"),
    ("弱口令登录", "web", "easy", 100, "管理后台登录页，试一下常见弱口令。提示：admin/admin 类", "flag{w3b_w3ak_p4ssw0rd}"),
    ("Cookie 伪造", "web", "easy", 100, "登录后 Cookie 里有个 role=guest，改成 admin 试试", "flag{w3b_c00k1e_f0rg3}"),
    ("URL 路径跳转", "web", "easy", 100, "点一个链接跳到别的页面，看看参数能不能改成 /flag", "flag{w3b_p4r4m_jump}"),
    ("源码注释泄露", "web", "easy", 100, "查看页面源码，注释里好像藏了点东西", "flag{w3b_s0urc3_c0mm3nt}"),
    (" robots.txt 信息泄露", "web", "easy", 100, "访问 /robots.txt 看看搜索引擎被屏蔽了什么路径", "flag{w3b_r0b0ts_txt}"),
    ("目录扫描", "web", "easy", 100, "用 dirsearch 扫一下目录，发现一个 /hidden 路径", "flag{w3b_d1r_sc4n}"),
    ("反射型 XSS", "web", "medium", 200, "在搜索框输入 <script>alert(1)</script>，看有没有回显。拿到 flag 在 cookie 里", "flag{w3b_r3fl3ct_xss}"),
    ("DOM 型 XSS", "web", "medium", 200, "hash 变化会改变页面内容，试试注入 location.hash", "flag{w3b_d0m_xss}"),
    ("SQL 联合查询", "web", "medium", 250, "id=1 存在注入，用 ORDER BY 判断列数，再 UNION 查 flag 表", "flag{w3b_sql_uni0n}"),
    ("SQL 报错注入", "web", "medium", 250, "页面会回显数据库报错，extractvalue/updatexml 了解一下", "flag{w3b3_sql_err}"),
    ("SQL 布尔盲注", "web", "medium", 300, "页面只显示正常/异常，没有报错。用 substr+ascii 逐字符猜", "flag{w3b_sql_bl1nd}"),
    ("文件包含", "web", "medium", 250, "?page=home 参数可控，试试 LFI 读 /flag", "flag{w3b_lfi_1nclude}"),
    ("文件上传前端绕过", "web", "medium", 250, "上传页面只在前端校验后缀，改包传 .php 试试", "flag{w3b_upl04d_byp4ss}"),
    ("文件上传 Content-Type 绕过", "web", "medium", 250, "后端校验 Content-Type，改成 image/jpeg 再传", "flag{w3b_upl04d_ct}"),
    ("SSRF 探测内网", "web", "medium", 300, "url 参数会去请求这个地址，试试 http://127.0.0.1:6379", "flag{w3b_ssrf_l0c4l}"),
    ("CSRF 修改邮箱", "web", "medium", 200, "修改邮箱接口没有 token，构造一个自动提交的页面", "flag{w3b_csrf_m4il}"),
    ("JWT 弱密钥", "web", "medium", 300, "JWT 用了弱密钥 secret，hashcat 爆破后改成 admin", "flag{w3b_jwt_w3ak}"),
    ("PHP 反序列化", "web", "hard", 400, "unserialize($_GET['data'])，__wakeup 里有命令执行", "flag{w3b_php_unser}"),
    ("SSTI 模板注入", "web", "hard", 400, "页面直接渲染 name 参数，Jinja2 模板注入试试 {{7*7}}", "flag{w3b_sst1_j1nj4}"),
    ("表达式注入", "web", "hard", 400, "Druid / SpEL / OGNL 任意一种，找到入口弹个计算器", "flag{w3b_3xpr3_ss1}"),
    ("XXE 读取文件", "web", "hard", 400, "XML 解析没禁用外部实体，读 /flag", "flag{w3b_xx3_f1l3}"),
    ("Redis 未授权写 SSH Key", "web", "hard", 500, "6379 未授权，写公钥到 /root/.ssh/authorized_keys", "flag{w3b_r3d1s_ssh}"),
    ("Nginx 解析漏洞", "web", "hard", 400, "/upload/test.jpg/.php 会被当作 PHP 执行", "flag{w3b_ng1nx_p4rse}"),
    ("逻辑漏洞密码重置", "web", "medium", 250, "找回密码流程中验证码可被预测/复用", "flag{w3b_l0g1c_r3s3t}"),
]

MISC = [
    ("Base64 一层", "misc", "easy", 100, "把这个字符串解出来：ZmxhZ3tiYXNlNjRfMWVufQ==", "flag{base64_1en}"),
    ("Base32", "misc", "easy", 100, "解 Base32：MFRXT2LTOU3SAYLCNVYWKY3MMU======", "flag{b4s332_ok}"),
    ("Hex 编码", "misc", "easy", 100, "解十六进制：666c61677b6865785f656173797d", "flag{hex_easy}"),
    ("URL 编码", "misc", "easy", 100, "解 URL 编码：%66%6c%61%67%7b%75%72%6c%5f%65%61%73%79%7d", "flag{url_easy}"),
    ("二进制转文本", "misc", "easy", 100, "01100110 01101100 01100001 01100111{01100010 01101001 01101110}", "flag{bin}"),
    ("摩尔斯电码", "misc", "easy", 100, "--.- --- ...- . .-. -.- . --..-- - .... . .-. .", "flag{ Morse cipher }"),
    ("栅栏密码", "misc", "easy", 100, "栅栏 2 栏：F_l_a_g_{c_a_e_s_a_r}_", "flag{caesar}"),
    ("凯撒密码", "misc", "easy", 100, "位移 13：synt{pnrfne_13_ebg13}", "flag{caesar_13_rot13}"),
    ("ROT47", "misc", "easy", 100, "ROT47 加密：t=2DE?oD:?</script>~A", "flag{rot47_demo}"),
    ("手机九宫格键盘", "misc", "easy", 100, "数字对应键盘：2-3-4-5 6-7-8-9", "flag{testword}"),
    ("ASCII 表", "misc", "easy", 100, "十进制：102 108 97 103 123 97 115 99 105 105 125", "flag{ascii}"),
    ("图片隐写 - LSB", "misc", "medium", 200, "用 stegsolve 看 PNG 最低有效位，QR 码扫一下", "flag{lsb_st3g0}"),
    ("图片尾数据", "misc", "medium", 200, "binwalk 分离图片尾部，得到一个压缩包", "flag{jpg_zip}"),
    ("ZIP 伪加密", "misc", "medium", 200, "改 ZIP 全局标记字节 09->00 就能解开", "flag{z1p_f4k3}"),
    ("ZIP 暴力破解", "misc", "medium", 200, "字典爆破 ZIP 密码，密码是 6 位纯数字", "flag{z1p_brut3}"),
    ("Wireshark 流量包", "misc", "medium", 250, "分析 pcap 文件，跟着 TCP 流找到 flag", "flag{p4cp_tr4c3}"),
    ("流量中的 HTTP 传输", "misc", "medium", 250, "过滤 http.request，找 POST 包", "flag{http_p0st}"),
    ("二维码遮罩", "misc", "medium", 200, "图片上有一半被涂黑，补全后扫码", "flag{qr_p4rt14l}"),
    ("音频频谱图", "misc", "hard", 300, "用 Audacity 打开 wav，切到频谱图模式", "flag{sp3ctr0gr4m}"),
    ("摩尔斯音频", "misc", "hard", 300, "听音频长短音，对照摩尔斯表", "flag{audi0_m0rs3}"),
    ("PDF 隐藏图层", "misc", "hard", 300, "PDF 有隐藏图层，打开图层面板", "flag{pdf_l4y3r}"),
    ("EXIF 信息", "misc", "easy", 100, "exiftool 看图片元数据", "flag{ex1f_m3t4}"),
    ("NTFS 数据流", "misc", "hard", 400, "在 NTFS 文件系统里找交替数据流", "flag{ntfs_ads}"),
    ("内存取证", "misc", "hard", 400, "volatility 分析 memdump，找浏览器密码", "flag{m3m_f0r3ns1c}"),
    ("磁盘镜像", "misc", "hard", 400, "用 autopsy 挂载 img，找被删除的文件", "flag{d1sk_1mg}"),
]

CRYPTO = [
    ("单表替换", "crypto", "easy", 100, "密文是字母表乱序替换，频率分析", "flag{subst_c1ph3r}"),
    ("维吉尼亚", "crypto", "medium", 200, "密钥是 KEY，解密 Vigenere", "flag{v1g3n3r3}"),
    ("仿射密码", "crypto", "medium", 200, "ax+b mod 26，已知两对明密文", "flag4ff1ne}"),
    ("DES ECB", "crypto", "medium", 250, "已知 key，解 DES ECB", "flag{d3s_3cb}"),
    ("AES ECB", "crypto", "medium", 250, "AES-128-ECB，key 全 0", "flag{43s_3cb}"),
    ("AES CBC 字节翻转", "crypto", "hard", 400, "CBC 模式翻转密文块修改明文", "flag{43s_cbc_fl1p}"),
    ("RSA 小 e", "crypto", "hard", 400, "e=3，密文小于 n，直接开立方根", "flag{rs4_sm4ll_3}"),
    ("RSA 共模攻击", "crypto", "hard", 500, "两份密文用同一个 n 不同 e", "flag{rs4_c0mm0d}"),
    ("RSA 低私钥指数", "crypto", "hard", 500, "Wiener 定理，d 太小连分数攻击", "flag{rs4_w13n3r}"),
    ("RSA 因式分解", "crypto", "medium", 300, "n 太小， factordb 直接查", "flag{rs4_fact0r}"),
    ("XOR 单次密钥", "crypto", "medium", 200, "已知明密文对，恢复密钥", "flag{x0r_0n3t1m3}"),
    ("XOR 多表", "crypto", "medium", 200, "多段密文用同一段密钥，crib dragging", "flag{x0r_r3us3}"),
    ("Base64 套娃", "crypto", "easy", 100, "解一层还是 Base64，连续解 5 次", "flag{b64_n3st}"),
    ("培根密码", "crypto", "medium", 200, "ABAB 串对应培根字母表", "flag{b4c0n_c0d3}"),
    ("波利比奥斯方阵", "crypto", "medium", 200, "5x5 方阵坐标", "flag{p0lyb1us}"),
    ("希尔密码", "crypto", "medium", 250, "矩阵求逆解密 Hill", "flag{h1ll_c1ph3r}"),
    ("椭圆曲线", "crypto", "hard", 500, "ECC 离散对数，P=kG 求 k", "flag{3cc_dl0g}"),
    ("离散对数", "crypto", "hard", 500, "p-1 光滑，Pohlig-Hellman", "flag{dh_p0hlig}"),
    ("Miller-Rabin", "crypto", "medium", 200, "用 Miller-Rabin 判断素数", "flag{m1ll3r_r4b1n}"),
    ("MD5 碰撞", "crypto", "medium", 300, "两个不同文件 MD5 相同", "flag{md5_c0ll1s10n}"),
    ("SHA1 长度扩展", "crypto", "hard", 400, "长度扩展攻击伪造签名", "flag{sh4_l3ng3xt}"),
    ("脑钱包", "crypto", "hard", 400, "私钥是常用口令的哈希", "flag{br41nw4ll3t}"),
    ("Padding Oracle", "crypto", "hard", 500, "CBC padding oracle 逐字节解密", "flag{p4dd1ng_0r4cl3}"),
    ("古典密码 - Atbash", "crypto", "easy", 100, "Atbash 反转字母表", "flag{4tb4sh}"),
    ("键盘移位", "crypto", "easy", 100, "QWERTY 键盘右移一位", "flag{k3yb04rd}"),
]

REVERSE = [
    ("ELF hello", "reverse", "easy", 100, "file 看一下，strings 找 flag", "flag{r3v_3lf_h3ll0}"),
    ("Windows PE hello", "reverse", "easy", 100, "用 Dependency Walker 看字符串", "flag{r3v_p3_h3ll0}"),
    ("无壳 64 位", "reverse", "easy", 150, "IDA 打开看 main 函数 strcmp", "flag{r3v_n0p4ck}"),
    ("UPX 脱壳", "reverse", "easy", 200, "upx -d 直接脱", "flag{r3v_upx}"),
    ("简单异或", "reverse", "medium", 200, "main 里对输入做 XOR 然后比较", "flag{r3v_x0r}"),
    ("简单加密比较", "reverse", "medium", 200, "输入经过一次变换后和密文比较", "flag{r3v_tr4nsf0rm}"),
    ("动态调试断点", "reverse", "medium", 250, "gdb 在 strcmp 处断下，看 RSI", "flag{r3v_dd_bp}"),
    ("Frida Hook", "reverse", "hard", 350, "Android so 里的校验函数 hook 掉", "flag{r3v_fr1d4}"),
    ("Java 反编译", "reverse", "medium", 250, "jadx 打开 apk 找 MainActivity", "flag{r3v_j4d3x}"),
    ("IL 反编译", "reverse", "medium", 200, "dnSpy 打开 .NET exe", "flag{r3v_dnspy}"),
    ("控制流平坦化", "reverse", "hard", 400, "花指令打乱，恢复控制流", "flag{r3v_fl4tt3n}"),
    ("花指令", "reverse", "hard", 400, "nop 掉垃圾指令", "flag{r3v_junk}"),
    ("VM 虚拟化", "reverse", "hard", 500, "自实现字节码虚拟机，先逆指令集", "flag{r3v_vm}"),
    ("ARM 汇编", "reverse", "hard", 400, "arm-linux-gnueabi 交叉编译", "flag{r3v_4rm}"),
    ("MIPS 汇编", "reverse", "hard", 400, "路由器固件常见架构", "flag{r3v_m1ps}"),
    ("Go 二进制", "reverse", "medium", 300, "Go 的符号表保留较多", "flag{r3v_g0}"),
    ("Rust 二进制", "reverse", "medium", 300, "Rust 符号剥离后比较痛苦", "flag{r3v_rust}"),
    ("Go Defer 坑", "reverse", "hard", 400, "defer 执行顺序陷阱", "flag{r3v_g0_d3f3r}"),
    ("算法还原 - RC4", "reverse", "medium", 300, "逆出 RC4 密钥流", "flag{r3v_rc4}"),
    ("算法还原 - DES", "reverse", "hard", 400, "逆出 DES 子密钥", "flag{r3v_d3s}"),
    ("算法还原 - AES Tbox", "reverse", "hard", 400, "找 sbox 常量识别 AES", "flag{r3v_43s}"),
    ("Patch 跳过校验", "reverse", "easy", 150, "jz 改 jmp 直接跳到 success", "flag{r3v_p4tch}"),
    ("补丁注册机", "reverse", "medium", 250, "写一个注册机算正确 key", "flag{r3v_k3yg3n}"),
    ("反调试检测", "reverse", "hard", 400, "IsDebuggerPresent / ptrace 反调试", "flag{r3v_4nt1dbg}"),
    ("字符串加密", "reverse", "medium", 200, "运行时解密字符串，动态 dump", "flag{r3v_str3nc}"),
]


def seed():
    if Challenge.query.count() > 0:
        return
    all_challenges = WEB + MISC + CRYPTO + REVERSE
    for tup in all_challenges:
        title, cat, diff, score, desc, flag = tup
        db.session.add(Challenge(
            title=title, category=cat, difficulty=diff,
            description=desc, flag=flag, score_value=score,
        ))
    # 管理员 + 默认战队
    t = Team(name="DemoTeam")
    db.session.add(t)
    db.session.commit()
    admin = User(username="admin",
                 password_hash=generate_password_hash("admin123"),
                 team_id=t.id, role="admin")
    db.session.add(admin)
    db.session.commit()
    print(f"[seed] inserted {len(all_challenges)} challenges, admin/admin123 (role=admin)")
