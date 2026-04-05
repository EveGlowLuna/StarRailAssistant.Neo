<p align="center"><img src="resources/SRAico.png" alt="icon"></p>
<p align="center">
    <img src="https://img.shields.io/badge/platform-Windows-blue" alt="platform">
    <img alt="Static Badge" src="https://img.shields.io/badge/python-3.12-skyblue">
    <img alt="GitHub Release" src="https://img.shields.io/github/v/release/EveGlowLuna/StarRailAssistant-CommunityEdition">
    <img alt="status" src="https://img.shields.io/badge/维护-缓慢/停滞-yellow">
</p>

> [!WARNING]
> 正在为Linux平台的运行做铺垫，项目处于**缓慢开发**状态。你可以从源码运行（现已支持基本功能），但注意由于Linux平台的特殊性，并未对Linux平台实现**游戏启动**的功能。请自行前往GitHub查找启动器

# StarRailAssistant.Neo

崩坏星穹铁道自动化助手（社区版太过个人，个人版太过社区，故改名；原SRA-CE）

原架构（Tauri）太难跟进，故与原版保持一致。

## 项目简介

这是基于 [StarRailAssistant](https://github.com/Shasnow/StarRailAssistant) 的二次开发版本，为 Linux 提供支持

## 什么是 SRA？

一个基于图像识别的崩铁自动化程序，帮您完成从启动到退出的崩铁日常。

## 免责声明

本软件是一个外部工具旨在自动化 崩坏：星穹铁道 的游戏玩法。它被设计成仅通过现有用户界面与游戏交互,并遵守相关法律法规。该软件包不打算以任何方式破坏游戏平衡或提供任何不公平的优势。该软件包不会以任何方式修改任何游戏文件或游戏代码。

This software is open source, free of charge and for learning and exchange purposes only. The developer team has the final right to interpret this project. All problems arising from the use of this software are not related to this project and the developer team. If you encounter a merchant using this software to practice on your behalf and charging for it, it may be the cost of equipment and time, etc. The problems and consequences arising from this software have nothing to do with it.

本软件开源、免费，仅供学习交流使用。开发者团队拥有本项目的最终解释权。使用本软件产生的所有问题与本项目与开发者团队无关。若您遇到商家使用本软件进行代练并收费，可能是设备与时间等费用，产生的问题及后果与本软件无关。

请注意，根据 MiHoYo 的 [崩坏:星穹铁道的公平游戏宣言](https://sr.mihoyo.com/news/111246?nav=news&type=notice):

    "严禁使用外挂、加速器、脚本或其他破坏游戏公平性的第三方工具。"
    "一经发现，米哈游（下亦称"我们"）将视违规严重程度及违规次数，采取扣除违规收益、冻结游戏账号、永久封禁游戏账号等措施。"

## 功能特性

* **启动游戏**
    * 选择游戏路径，输入账号与密码，程序会帮你解决好一切。已适配 B 服。
* **清体力**
    * 自由选择关卡，设置是否补充体力、连战次数、执行次数，支持混合搭配。
* **领取奖励**
    * 包括：每日实训、无名勋礼、助战奖励、兑换码奖励、派遣奖励、巡星之礼、邮件奖励等。
* **差分宇宙刷等级**
* **货币战争**
* **退出游戏**
    * 可选退出 SRA 以及关闭计算机。
* **自动剧情**
    * 解放双手，享受剧情，支持跳过。
* **多账号切换**

## 快速开始

> 目前还没有最新版的Release,尽请期待。

### 下载安装

前往 [Releases](https://github.com/EveGlowLuna/StarRailAssistant.Neo/releases/latest) 或 [AList](https://alist.starrailassistant.xyz/) 页面下载最新版本.

### 使用方法

1. 下载并安装
2. 在开始菜单或桌面打开 `StarRailAssistant`
3. 配置游戏路径和账号信息
4. 选择需要执行的任务
5. 点击开始，坐和放宽

### 注意事项

* **调整游戏分辨率为 1920×1080（推荐）或16:9比例窗口（必须）并保持游戏窗口无遮挡，不要让游戏窗口超出屏幕**
* **执行任务时不要进行其他键鼠操作！**
* **菜单要用初始壁纸**

## 反馈与支持

如果您在使用过程中遇到问题或有建议，欢迎通过以下方式反馈：

* 通过 **Issues** 反馈：[提交 Issue](https://github.com/EveGlowLuna/StarRailAssistant.Neo/issues)
* 通过 **Pull Request** 贡献代码

## 贡献指南

请查看[贡献指南](CONTRIBUTING.md)

## 致谢

本项目基于 [StarRailAssistant](https://github.com/Shasnow/StarRailAssistant) 开发，感谢原作者 Shasnow 及所有贡献者的付出。

## 开源协议

本项目采用 GPL-3.0 协议开源，详见 [LICENSE](LICENSE) 文件。

---

**注意**：本项目仅供学习交流使用，请勿用于商业用途。使用本软件产生的一切后果由使用者自行承担。
