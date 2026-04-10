import pymem
import pymem.process

def peek():
    pm = pymem.Pymem("Lords Mobile PC.exe")
    module = pymem.process.module_from_name(pm.process_handle, "GameAssembly.dll")
    base = module.lpBaseOfDll
    
    # RVA de get_Instance
    addr = base + 0x1CD1140
    data = pm.read_bytes(addr, 16)
    print(f"BYTECODE_GET_INSTANCE: {data.hex()}")

peek()
