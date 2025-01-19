# KookTicketBot4SMC -- Ticket bot for smc using on Kook
--- 

这是一个简易改造Kook服务器为客服系统的机器人。

最初应UncleSn的邀请给SimMC服务器开发的开票机器人，用于处理服务器中的各项问题。

## 1 功能手册
> 机器人指令请使用`/`开头, 参数使用中括号标出。

- `setup [role tag]`

机器人发送一条消息，该消息包含一个按钮，点击后创建仅对应tag可见的Ticket

- `setrole [role tag]`

机器人发送卡片消息，点击对应角色可以为其标记。需要注意，每个角色只有一个tag，重复标记时后标记的数据会覆盖先前的数据。

- `listrole`

管理员功能，列出当前服务器全部角色和对应tag关系。

- `mute [user id]`

禁言用户，用户id使用kook自带的开发者模式查看。具体操作为：开启开发者模式，右键点击想禁言的用户，点击复制id。

- `unmute [user id]`

取消禁言，同上

- `man [manul file]`

机器人发送对应的手册文件，文件为markdown格式，若不指定则发送Readme。

- `clean [user id]`

清除用户在本服务器申请ticket的数据，用于在程序出Bug时补救。

- `rename [name]`

重命名当前频道

- `dice [n]` 或者 `d [n]`

骰一个骰子，n是骰子的面数

- `generate [-n (optional) numbers to generate] [bot commands]`

生成CDK,用户使用配套的 `activate` 指令可以使用CDK生成时指定的指令。
注意，在CDK由机器人生成后会自动回复， 此CDK仅展示给发送指令的人，并在离开频道时消失，请及时保存。
此外，CDK格式为UUID。

- `activate [CDK]`

使用这条指令来激活一条CDK。

## 2 部署指南

### 2.1 环境准备：
- 一台能够链接网络的计算机
- Python >= 3.6.8
- 使用pip安装khl.py模块：

如果您的操作系统是Windows，并安装Python或Conda环境；或已自行修改过Linux的Python链接，请使用：
```shell
pip install khl.py
```
如果您的操作系统是原生Linux,可能需要使用这条命令：
```shell
pip3 install khl.py
```

- 另注：推荐具有一定计算机能力与Python编程知识（起码会解决pip问题）的用户尝试部署本产品。

1. 将项目所有源代码打包下载到待部署的服务器中，并解压至任意空文件夹。
2. 根据*3 文件结构*中所示树形图文件结构，新建cfg文件夹和man文件夹。其中，man文件夹应置于cfg文件夹中。
3. 新建config.json文件，在其中填写对应配置项。（其他文件会随软件运行自动生成，首次运行时请不要新建，容易使程序报错。）
4. 根据你的操作系统，运行对应的bat文件。（由于技术问题目前没有后台运行文件，如有需求，请自行修改bat文件。） 

以下为config文件填写示例：
```json
{
  "token" : "你的机器人Token，请到Kook的开发者网站查询 https://developer.kookapp.cn/app/index"
}
```

## 3 文件结构
为了能对Ticket系统有一个明确的体系结构上的认识，在这里将整个文件的目录列举出来。

在之前架构的时候脑子一抽就用了类~~MVC(大概)~~的模式，service中都是数据的增删改查相关的代码主要涉及到文件读写；controller中写的主要是逻辑代码。

请注意，有部分文件目录没有被上传至Github的项目中，如果您需要部署本机器人至您的服务器，请自行创建相关目录。
```
.
├── cfg  
│    ├── man                        | 放置各种手册文件，用于/man指令调用。  
│    │   └─ manual.txt              | 默认的帮助文件，请您在部署机器人时自行创建。
│    ├── config.json                | 各种配置文件, 包含机器人的Token等  
│    ├── data.json                  | 这里存储了各个服务器的数据，主要是角色和权限配置。  
│    ├── mute.json                  | 这里存储了被禁言用户的数据。
│    ├── cdk.json                   | 这里放着已经申请的所有CDK。
│    └── user.json                  | 存储了某个用户在某个服务器累计开出多少张Ticket。
│     
├── log                             | 存放日志文件的目录。
│     
├── py  
│    ├── guild_service.py  
│    ├── manual_controller.py
│    ├── mute_controller.py  
│    ├── mute_service.py  
│    ├── parser.py                  | 用于处理数据的逻辑，很多都是格式化用的  
│    ├── ticket_controller.py  
│    ├── user_service.py  
│    ├── utils.py                   | 工具函数集合
│    └── value.py                   | 这里放着所有配置用的常量。若要进行自定义配置文件路径(cfg目录)、自定义角色等操作，请在部署项目时请根据实际情况修改。  
├── bot.py                          | 机器人的核心程序代码
└── startbot.bat                    | 运行该文件启动机器人，请使用对应操作系统的启动文件。 
```

---

# 附录 Config文件的内容

简体中文：
```json
{
  "token": "你的机器人的Token",  
  "activate_gap":"[这是可选项]激活CDK的冷却时间（单位：秒）， 默认3600秒",
  "create_ticket_role": "[这是可选项]填一个服务器中的角色，有这个角色的人才能开票。",
  "new_ticket": "[这是可选项]新开的票会自动发送这里的消息。",
  "default_ticket_number": "[这是可选项]每个人最大开票数量，默认为2"
}
```

英文：
```json
{
  "token": "Your bot's token",  
  "activate_gap":"[Opt]User's CDK activate time gap (seconds), default 3600s",
  "create_ticket_role": "[Opt]If defined, only users has this role can create ticket",
  "new_ticket": "[Opt]Message will automatically send when ticket is created",
  "default_ticket_number": "[Opt]Maximum tickets could be applied per user, default 2"
}
```

 
