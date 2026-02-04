# ES2 WebMUD 项目概览

## 项目简介
这是一个基于 **ES2 (Eastern Stories 2, 东方故事2)** Mudlib 的 MUD (Multi-User Dungeon) 游戏项目。项目旨在维护经典的中文 MUD 内容，并为其开发现代化的访问接口（Web 和 Python 客户端）。

## 核心组成部分

### 1. 游戏内容库 (Mudlib)
*   **位置**: `mudlib/`
*   **描述**: 包含游戏世界 (`d/`)、指令 (`cmds/`)、系统后台 (`daemon/`) 等 LPC (LPMud C) 代码。
*   **作用**: 这是游戏的核心规则、故事和数据所在。

### 2. 游戏驱动 (Driver)
*   **位置**: `fluffos_src/`, `bin/`
*   **技术**: **FluffOS** (MudOS 的现代分支)。
*   **作用**: 服务器端驱动程序，用于解释和运行 Mudlib 中的代码。

### 3. 客户端实现

#### Web 客户端
*   **位置**: `webmud/`
*   **技术**: Node.js & HTML5。
*   **目标**: 让玩家可以通过浏览器（包括手机微信/QQ内置浏览器）直接玩 MUD，无需传统 Telnet 客户端。

#### Python 客户端 (开发中)
*   **位置**: `mud_client.py`
*   **技术**: Python 3 (socket, readline)。
*   **状态**: 活跃开发中。
*   **功能**:
    *   作为轻量级的命令行客户端替代 Telnet。
    *   支持 UTF-8 编码。
    *   **近期工作**:
        *   解决中文输入和显示乱码问题。
        *   实现日志记录 (Logging) 功能。
        *   重构连接和交互逻辑。

## 近期开发重点
1.  **编码适配**: 确保项目整体从旧的 Big5 等编码迁移并适配 **UTF-8**。
2.  **客户端调试**: 完善 `mud_client.py` 以便更好地进行本地测试和游玩。
3.  **日志分析**: 通过客户端日志清洗乱码，分析游戏输出。

## 常用命令
*   **启动服务器**: `./bin/startmud`
*   **停止服务器**: `./bin/stopmud`
*   **运行 Python 客户端**: `python3 mud_client.py <host> <port>` (通常是 localhost 4000 或类似端口)
