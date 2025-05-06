import struct
import binascii
import os

def analyze_lua_bytecode(hex_data):
    # Convert hex string to bytes
    try:
        binary_data = bytes.fromhex(hex_data)
        
        # Lua 5.1 bytecode header starts with 0x1B4C7561 (ESC + "Lua")
        LUA51_HEADER = b'\x1B\x4C\x75\x61'
        LUA52_HEADER = b'\x1B\x4C\x75\x61\x52'  # Lua 5.2
        LUA53_HEADER = b'\x1B\x4C\x75\x61\x53'  # Lua 5.3
        
        # Save the binary data for inspection
        with open('bytecode.bin', 'wb') as f:
            f.write(binary_data)
        
        # Check for Lua bytecode headers
        if binary_data.startswith(LUA51_HEADER):
            print("Found Lua 5.1 bytecode header")
            version = "5.1"
        elif binary_data.startswith(LUA52_HEADER):
            print("Found Lua 5.2 bytecode header")
            version = "5.2"
        elif binary_data.startswith(LUA53_HEADER):
            print("Found Lua 5.3 bytecode header")
            version = "5.3"
        else:
            print("No standard Lua bytecode header found")
            
            # Print first 16 bytes for inspection
            print("First 16 bytes:", binascii.hexlify(binary_data[:16]).decode())
            
            # Try to identify potential instruction patterns
            # Lua instructions are typically 32-bit (4 bytes)
            for i in range(0, min(len(binary_data), 64), 4):
                instruction = binary_data[i:i+4]
                if len(instruction) == 4:
                    opcode = instruction[0]
                    print(f"Potential instruction at offset {i}: {binascii.hexlify(instruction).decode()}")
                    print(f"Opcode: {opcode:02x}")

        # Look for string table markers
        # In Lua bytecode, strings often start with a size prefix
        string_candidates = []
        i = 0
        while i < len(binary_data) - 4:
            size = int.from_bytes(binary_data[i:i+1], byteorder='little')
            if 1 <= size <= 255:  # reasonable string length
                potential_string = binary_data[i+1:i+1+size]
                if all(32 <= b <= 126 for b in potential_string):  # printable ASCII
                    string_candidates.append(potential_string.decode('ascii', errors='ignore'))
            i += 1
            
        if string_candidates:
            print("\nPotential strings found:")
            for s in string_candidates[:10]:  # Show first 10 strings
                print(f"- {s}")

    except Exception as e:
        print(f"Error during analysis: {e}")

if __name__ == "__main__":
    # Read the hex output from our previous decode
    with open('../decode_lua.py', 'r') as f:
        content = f.read()
    
    # Run decoder and get hex output
    import sys
    sys.path.append('..')
    from decode_lua import decode_lua
    
    with open('../test.lua', 'r', encoding='utf-8') as f:
        lua_content = f.read()
    
    import re
    match = re.search(r"O\('([^']+)'\)", lua_content)
    if match:
        encoded_string = match.group(1)
        hex_result = decode_lua(encoded_string)
        if hex_result:
            print("\nAnalyzing decoded data as Lua bytecode...")
            analyze_lua_bytecode(hex_result)