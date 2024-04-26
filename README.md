# KookTicketBot4SMC -- Ticket bot for smc using on Kook
--- 
给SimMC开发的一款开票机器人

## 文件结构
为了能对Ticket系统有一个明确的体系结构上的认识，在这里将整个文件的目录列举出来。

在之前架构的时候脑子一抽就用了类~~MVC(大概)~~的模式，service中都是处理数据相关的代码，controller中写的都是逻辑代码。

请注意，有部分文件目录没有被上传至Github的项目中，如果您需要部署本机器人至您的服务器，请自行创建相关目录。

> /cfg
>  > /man
>  >  > 这里放置各种手册文件，用于/man指令调用。
>  >
>  > config.json - 各种配置文件, 包含机器人的Token, 密码等
>  >
>  > data.json - 这里存储了各个服务器的数据，主要是角色和权限配置。
>  >
>  > mute.json - 这里存储了被禁言用户的数据
>  >
>  > user.json - 存储了某个用户在某个服务器累计开出多少张Ticket。
> 
> /py
>  > guild_service.py 
>  >
>  > manual_controller.py
>  >
>  > mute_controller.py
>  >
>  > mute_service.py
>  >
>  > parser.py - 用于处理数据的逻辑，很多都是格式化用的
>  >
>  > ticket_controller.py
>  >
>  > user_service.py
>  >
>  > value.py - 这里放着所有配置用的常量。若要进行自定义配置文件路径(cfg目录)、自定义角色等操作，请在部署项目时请根据实际情况修改。
> 
> bot.py - 机器人的核心程序代码
>
> startbot.bat - 运行该文件启动机器人，请使用对应操作系统的启动文件。

## 功能手册
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