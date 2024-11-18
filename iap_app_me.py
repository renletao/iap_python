# -*- coding:utf-8 -*-
import binascii
import os
import sys

# STM32F030C8
# start_addr = 0x8001000
# end_crc_addr = 0x08004000 - 0x400
# end_addr = 0x08004000

# STM32G030F6
# start_addr = 0x8001800
# end_crc_addr = 0x8007800
# end_addr = 0x8008000

# STM32G031G8
# start_addr = 0x8002000
# end_crc_addr = 0x8002000+0x4000
# end_addr = end_crc_addr + 0x800

# UHF___CAN
# STM32G431
# start_addr = (0x8003000)
# end_crc_addr = (start_addr + 0xB000)
# end_addr = (end_crc_addr + 0x800)

# UHF___RS485
# STM32G431
# start_addr = (0x8002800)
# end_crc_addr = (start_addr + 0xB000)
# end_addr = (0x0800E000)

# STM32F030C8
# start_addr = 0x8001000
# end_crc_addr = 0x800FC00
# end_addr = 0x8010000

# STM32F030G4
# start_addr = 0x8002000
# end_crc_addr = 0x801D800
# end_addr = 0x801E000

# STM32G031G8U6
start_addr = 0x8002000
end_crc_addr = 0x8002000+0xA000
end_addr = end_crc_addr + 0x800

# ZTAG
# start_addr = 0x8001800
# end_crc_addr = 0x8001800+0x6800
# end_addr = end_crc_addr

bootloader_addr = 0x8000000
bootloader_version_addr = start_addr - 1
bootloader_version = 1

def crc2hex(crc):
    res=''
    for i in range(4):
        t=crc & 0xFF
        crc >>= 8
        res='%02X%s' % (t, res)
    return res

def main():
    # 文件路径输入
    if not sys.argv[1] or not sys.argv[2]:
        print("bin file error")
        return
    
    isbootloader = os.path.isfile(sys.argv[1])
    if not isbootloader:
        print("bootloader bin file error")
        return
    isapp = os.path.isfile(sys.argv[2])
    if not isapp:
        print("app bin file error")
        return
    print(sys.argv[1])


    # bootloader.bin & bootloader.c生成
    fp = open(sys.argv[1], "r+b")  #直接打开一个文件，如果文件不存在则创建文件
    filesize = os.path.getsize(sys.argv[1])
    write_0xff_len = bootloader_version_addr - bootloader_addr - filesize
    b_0xff = bytes([0xFF] * write_0xff_len)
    print("bootloader firmware size:", filesize, "bytes.")

    fp.seek(0, 0)
    file_content = fp.read()#读整个文件内容到 file_content
    fp.close()

    bootloader_content = file_content + b_0xff
    bootloader_version_content = bytes([bootloader_version])
    bootloader_with_version = bootloader_content + bootloader_version_content

    bootloaderBinListData = []
    for binByte in bootloader_with_version:
        bootloaderBinListData.append("0x%.2X" % binByte)
               
    # 将列表中的数据写入到 .h 源文件中
    fileOutput = open("bootloader.h", 'w')
    fileOutput.write("#pragma once\n")
    fileOutput.write("\n")
    fileOutput.write("#include <stdint.h>\n")
    fileOutput.write("// address:0x{:X} - 0x{:X}\n".format(bootloader_addr, start_addr))
    fileOutput.write("unsigned long bootloaderHexLength = 0x{:X};\n".format(start_addr - bootloader_addr))
    fileOutput.write("static const unsigned char bootloaderHexData[] = \n")
    fileOutput.write("{\n")
    for i in range(len(bootloader_with_version)):
        if (i != 0) and (i % 16 == 0):
            fileOutput.write("\n")
            fileOutput.write(bootloaderBinListData[i] + ",")
        elif (i + 1) == len(bootloader_with_version):
            fileOutput.write(bootloaderBinListData[i])
        else:
            fileOutput.write(bootloaderBinListData[i] + ",")            
    fileOutput.write("\n};")
    fileOutput.close()
    print("bin file to C array file success!!!")


    # app.bin & app.c生成
    print(sys.argv[2])
    fp = open(sys.argv[2], "r+b")  #直接打开一个文件，如果文件不存在则创建文件
    filesize = os.path.getsize(sys.argv[2])
    write_0xff_len = end_crc_addr - start_addr - filesize
    b_0xff = bytes([0xFF] * write_0xff_len)
    print("app firmware size:", filesize, "bytes.")

    file_content = fp.read()#读整个文件内容到 file_content
    
    fp.close()

    app_content = file_content + b_0xff

    app_cut_size = end_crc_addr - start_addr - 4
    app_content_crc = app_content[:app_cut_size]
    #计算bin文件的CRC，首先清空CRC32区域的4个byte
    
    crc = binascii.crc32(app_content_crc)
    crcstr_2 = crc2hex(crc)
    print('CRC32_HEX:0x' + crcstr_2)
    crc32_bytes=binascii.unhexlify(crcstr_2)[::-1]

    appWithoutFlashBinListData = []
    for binByte in app_content_crc+crc32_bytes:
        appWithoutFlashBinListData.append("0x%.2X" % binByte)
               
    # 将列表中的数据写入到 .h 源文件中
    fileOutput = open("app_without_flash.h", 'w')
    fileOutput.write("#pragma once\n")
    fileOutput.write("\n")
    fileOutput.write("#include <stdint.h>\n")
    fileOutput.write("// address:0x{:X} - 0x{:X}\n".format(start_addr, end_crc_addr))
    fileOutput.write("unsigned long appHexLength = 0x{:X};\n".format(end_crc_addr - start_addr))
    fileOutput.write("static const unsigned char appHexData[] = \n")
    fileOutput.write("{\n")
    for i in range(len(app_content_crc+crc32_bytes)):
        if (i != 0) and (i % 16 == 0):
            fileOutput.write("\n")
            fileOutput.write(appWithoutFlashBinListData[i] + ",")
        elif (i + 1) == len(app_content_crc+crc32_bytes):
            fileOutput.write(appWithoutFlashBinListData[i])
        else:
            fileOutput.write(appWithoutFlashBinListData[i] + ",")            
    fileOutput.write("\n};")
    fileOutput.close()
    print("bin file to C array file success!!!")    

    if end_addr > end_crc_addr:
        write_0xff_flash_area_len = end_addr - end_crc_addr
        flash_area = bytes([0xFF] * write_0xff_flash_area_len)
        fw = open('bootloader_app_merge.bin', "wb")
        fw.write(bootloader_with_version + app_content_crc + crc32_bytes + flash_area)
        fw.close()

        appWithFlashBinListData = []
        for binByte in app_content_crc+crc32_bytes+flash_area:
            appWithFlashBinListData.append("0x%.2X" % binByte)
                
        # 将列表中的数据写入到 .h 源文件中
        fileOutput = open("app_with_flash.h", 'w')
        fileOutput.write("#pragma once\n")
        fileOutput.write("\n")
        fileOutput.write("#include <stdint.h>\n")
        fileOutput.write("// address:0x{:X} - 0x{:X}\n".format(start_addr, end_addr))
        fileOutput.write("unsigned long appHexLength = 0x{:X};\n".format(end_addr - start_addr))
        fileOutput.write("static const unsigned char appHexData[] = \n")
        fileOutput.write("{\n")
        for i in range(len(app_content_crc+crc32_bytes+flash_area)):
            if (i != 0) and (i % 16 == 0):
                fileOutput.write("\n")
                fileOutput.write(appWithFlashBinListData[i] + ",")
            elif (i + 1) == len(app_content_crc+crc32_bytes+flash_area):
                fileOutput.write(appWithFlashBinListData[i])
            else:
                fileOutput.write(appWithFlashBinListData[i] + ",")            
        fileOutput.write("\n};")
        fileOutput.close()
        print("bin file to C array file success!!!")          
    else:
        fw = open('bootloader_app_merge.bin', "wb")
        fw.write(bootloader_with_version + app_content_crc + crc32_bytes)
        fw.close()

    res = os.popen("python C:/Users/15191/.espressif/python_env/idf5.1_py3.11_env/Scripts/bin2hex.py --offset=0x8000000 bootloader_app_merge.bin bootloader_app_merge.hex") 

if __name__ == '__main__':
    main()    