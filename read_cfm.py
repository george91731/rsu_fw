from smbus2 import SMBus, i2c_msg
import time

MAX10_I2C_SLAVE_ADDRESS = 0x55
I2C_BUS_NUMBER = 1

def read_memory(bus, address):    
    address_bytes = address.to_bytes(4, 'big')
    write_msg = i2c_msg.write(MAX10_I2C_SLAVE_ADDRESS, address_bytes)
    bus.i2c_rdwr(write_msg)    
    read_msg = i2c_msg.read(MAX10_I2C_SLAVE_ADDRESS, 4)
    bus.i2c_rdwr(read_msg)
    read_bytes = list(read_msg)
    print(f"Read bytes from addr {address:08X}:{''.join(f'{byte:02X}' for byte in read_bytes)}")
    data = int.from_bytes(read_bytes, 'big')
    return data

def read_flash_to_file(bus, file_path, START_ADDR, END_ADDR):
    addr = START_ADDR
    block = []
    with open(file_path, 'w') as f: 
        while addr <= END_ADDR:            
            data = read_memory(bus,addr)
            block.append(f'{data:08X}')
            if len(block) == 4:
                f.write(' '.join(block) + '\n')
                block = []
                print(f'data: {data:08X}')
            addr += 4
        if block:
            f.write(' '.join(block) + '\n')




def main():
    with SMBus(I2C_BUS_NUMBER) as bus:  
        read_flash_to_file(bus, 'Sbig_read_rpi.txt', 0x00008000, 0x0004dfff)



if __name__ == "__main__":
    main()