# Uptek 超快激光系统远程控制软件

超快激光光源的控制系统，基于 Uptek 生产的激光控制器自身的通讯协议和 [Labctrl](https://github.com/Astro-Aionia/CB331-Labctrl) 实验室控制框架。

Uptek 公司生产的超快激光激光系统由种子光 Aria 系列和啁啾脉冲放大器Phidia系列组成。Phidia 内部集成了泵浦光 Lucia 系列，由控制器 Phi 系列控制、以及普克尔盒，由高速电开关 Tau 系列控制。该套设备的控制面板采用了老旧的薄膜按键和旋钮等机械部件，容易损坏。另外，Phi 系列控制器对泵浦光的电流设置缺少必要的过冲保护，打开激光时的瞬间大电流容易加速二极管的损耗。因此利用计算机远程控制简化仪器操作并添加额外保护

## 功能特性

- 平滑升电实现过冲保护
- 前后端分离多重保护
- RESTful框架支持局域网控制

## 需求

### 硬件连接

Phi 系列控制器自带 RS232 协议，需要用串口线或串口转 usb 线连接至电脑。Tau 系列控制器只有 CAN 通讯接口，需要使用直连 DB9 电缆与 Phi 连接后，同一通过 Phi 的 RS232 接口控制。

```
     CAN       RS232
Tau ----- Phi ------- PC
```

### 软件环境

需要安装 Anacoda， 然后依次执行

```CMD
:: create new environment
conda create -n {your_env_name} python=3.11
conda activate {your_env_name}

:: intall necessary packages
pip install pyserial flask json

:: install pyqt. you can skip this if you want use your own front end.
pip install pyqt6
```

## 运行

1. 运行后端服务器

    修改 `server.bat`，使用你自己的环境名和端口。

    ```BAT
    CALL C:\ProgramData\Anaconda3\condabin\conda.bat activate {your_env_name}

    set FLASK_APP=cpa_server
    python -m flask run --port {your_port}

    ```

    运行

    ```CMD
    ./server.bat
    ```

2. 运行前端 GUI
    ```CMD
    python main.py
    ```