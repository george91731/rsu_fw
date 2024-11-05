from smbus2 import SMBus, i2c_msg
import time


MAX10_I2C_SLAVE_ADDRESS = 0x55
I2C_BUS_NUMBER = 1

def reverse_bytes(data):
    byte_array = data.to_bytes(4, 'big')
    return int.from_bytes(byte_array[::-1], 'big')

def write_data(bus, address, data):   
    address_bytes = list(address.to_bytes(4, 'big'))
    data_bytes = list(reverse_bytes(data).to_bytes(4, 'big'))
    packets = address_bytes + data_bytes
    print(f'Writing to address {address:08X}: data {data:08X}')
    print(f'Sending packets: {" ".join(f"{byte:02X}" for byte in packets)}')  
    msg = i2c_msg.write(MAX10_I2C_SLAVE_ADDRESS, packets)
    bus.i2c_rdwr(msg)

def erase_sector(bus, address, data):
    write_data(bus, address, data)

def read_busy_bit(bus, address):    
    address_bytes = address.to_bytes(4, 'big')
    print(f'Sending address for reading busy bit check: {" ".join(f"{byte:02X}" for byte in address_bytes)}') 
    write_msg = i2c_msg.write(MAX10_I2C_SLAVE_ADDRESS, address_bytes)
    bus.i2c_rdwr(write_msg) 

    read_msg = i2c_msg.read(MAX10_I2C_SLAVE_ADDRESS, 4)
    
    bus.i2c_rdwr(read_msg)
    read_bytes = list(read_msg)
    print(f'Read bytes: {" ".join(f"{byte:02X}" for byte in read_bytes)}')

    # reverse read bytes
    reversed_bytes = bytes(read_bytes[::-1])
    busy_bit = int.from_bytes(reversed_bytes, 'big')
    
    # check bit1-0 = 00
    print(f'Busy bit value at address {address:08X} after reverse: {busy_bit:08X}')
    if (busy_bit & 0x3) == 0x0:
        print(f'Slave is idle')
        return True  
    else:
        print(f'Slave is busy')
        return False
            
def program_flash(bus, addr, data):    
    outbuf = bytearray(8)
    outbuf[0] = (addr >> 24) & 0xFF
    outbuf[1] = (addr >> 16) & 0xFF
    outbuf[2] = (addr >> 8) & 0xFF
    outbuf[3] = addr & 0xFF
    outbuf[4:] = data
    msg = i2c_msg.write(MAX10_I2C_SLAVE_ADDRESS, outbuf)
    print(f'Sending packets: {" ".join(f"{byte:02X}" for byte in outbuf)}')  
    bus.i2c_rdwr(msg)
    
def program_flash_from_file(bus, file_path, START_ADDR, END_ADDR):
    addr = START_ADDR

    with open(file_path, 'r') as f: 
        for line in f:                   
            
            hex_data_part = line[5:54].strip()  
            hex_data = hex_data_part.split()          
            print(f'Extracted hex data: {hex_data}')
            
            for i in range(0, len(hex_data), 4):
                if addr >= END_ADDR:
                    print(f'Reached end address: {addr:08X}')
                    return
                if i + 3 >= len(hex_data):
                    break
                               
                data_bytes = bytes(int(hex_data[j], 16) for j in range(i, i+4))
                
                if len(data_bytes) != 4:
                    print(f'Invalid data length: {len(data_bytes)} for data: {data_bytes.hex().upper()}')
                    continue

                print(f'Programming addr {addr:08X} with data {data_bytes.hex().upper()}')                
                reversed_bytes = bytes(data_bytes[::-1])
                program_flash(bus, addr, reversed_bytes)
                time.sleep(0.0001)

                while not read_busy_bit(bus, 0x00200020):
                    print('check if busy...')
                  
                addr += 4 
   

def main():
    with SMBus(I2C_BUS_NUMBER) as bus:  
        ######################################Image 2 flow######################################
        # 1. un-protect sector 3 & 4
        write_data(bus, 0x00200024, 0xf9ffffff)     
        
        # 2.  erase Sector3
        erase_sector(bus, 0x00200024, 0xf9bfffff)        
        
        # 3. check busy bit
        while not read_busy_bit(bus, 0x00200020):
            print('Still busy...')         
        
        # 4. erase Sector4
        erase_sector(bus, 0x00200024, 0xf9cfffff)       
        
        # 5. check busy bit
        while not read_busy_bit(bus, 0x00200020):
            print('Still busy...')            
        
        # 6. write erase sector bits to default
        write_data(bus, 0x00200024, 0xf9ffffff)   
        
        # 7. program flash
        program_flash_from_file(bus, 'Dbig_cfm1_auto.txt', 0x00008000, 0x0002afff)         
      
        # 8. re-protect
        write_data(bus, 0x00200024, 0xffffffff)
        
        
        ######################################Image 2 flow######################################

        ######################################Image 1 flow######################################
        # 1. un-protect sector 5
        write_data(bus, 0x00200024, 0xf7ffffff)     
        
        # 2.  erase Sector5
        erase_sector(bus, 0x00200024, 0xf7dfffff)        
        
        # 3. check busy bit
        while not read_busy_bit(bus, 0x00200020):
           print('Still busy...')             
         
        # 4. write erase sector bits to default
        write_data(bus, 0x00200024, 0xf7ffffff)   
        
        # 5. program flash
        program_flash_from_file(bus, 'Dbig_cfm0_auto.txt', 0x0002b000, 0x0004dfff) 
 

        # 8. re-protect
        write_data(bus, 0x00200024, 0xffffffff)      

        #####################################Image 1 flow######################################
        # # re-configure
        # write_data(bus, 0x00200004, 0x00000001)
        # time.sleep(0.1)

if __name__ == "__main__":
    main()
